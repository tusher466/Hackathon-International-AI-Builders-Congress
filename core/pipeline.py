"""Wires ingestion -> detection -> agents."""
from __future__ import annotations

import asyncio
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from config.settings import get_settings
from ingestion.schemas import SensorReading
from ingestion.cleaner import Cleaner
from ingestion.feature_extractor import FeatureExtractor
from ingestion.stream_simulator import StreamSimulator, get_memory_queue
from ingestion.consumer import StreamConsumer

from detection.anomaly_model import AnomalyModel
from detection.rul_model import RULModel
from detection.defect_model import DefectModel
from detection.alert_builder import AlertBuilder

from storage.db import get_db, init_db
from storage.timeseries_db import get_ring_buffer
from storage.repositories import save_reading, save_alert, save_trace, save_ticket, save_approval

from core.event_bus import get_event_bus

from knowledge.vector_store import get_vector_store
from knowledge.ingest_docs import ingest_manuals

from actions.ticketing import create_ticket
from actions.notifier import notify_event
from actions.approval import create_approval_request

from agents.graph import run_alert

logger = logging.getLogger(__name__)


class Pipeline:
    """Main pipeline: clean -> store -> ring buffer -> feature extraction -> detection -> agent graph."""

    def __init__(self):
        self.settings = get_settings()
        self.cleaner = Cleaner()
        self.feature_extractor = FeatureExtractor(window_size=self.settings.FEATURE_WINDOW_SIZE)
        self.anomaly_model = AnomalyModel()
        self.rul_model = RULModel()
        self.defect_model = DefectModel()
        self.alert_builder = AlertBuilder()
        self.ring_buffer = get_ring_buffer()
        self.event_bus = get_event_bus()

        self.simulator: Optional[StreamSimulator] = None
        self.consumer: Optional[StreamConsumer] = None
        self._sim_task: Optional[asyncio.Task] = None
        self._semaphore = asyncio.Semaphore(self.settings.MAX_CONCURRENT_AGENT_RUNS)

        # metrics for impact aggregated
        self._impact_metrics: Dict[str, float] = {
            "downtime_avoided": 0.0,
            "defects_prevented": 0,
            "energy_saved": 0.0,
            "alerts_by_severity": {},
            "auto_resolved": 0,
            "human_approved": 0,
        }
        self._total_diagnosis_time_ms = 0
        self._diagnosis_count = 0

    async def init(self) -> None:
        """Init DB, load models, init vector store, start consumer."""
        logger.info("Pipeline init")
        init_db()

        # Try load models, train automatically if missing
        if not self.anomaly_model.load(self.settings.MODELS_DIR):
            logger.warning("No anomaly models found, training with synthetic data")
            await self._train_models_simple()

        if not self.rul_model.load(self.settings.MODELS_DIR):
            logger.warning("No RUL model found, already handled in train")

        if not self.defect_model.load(self.settings.MODELS_DIR):
            logger.warning("No defect model found")

        # Cleaner scalers and feature extractor baselines
        self.cleaner.try_load_from_joblib(self.settings.MODELS_DIR)
        self.feature_extractor.try_load_from_joblib(self.settings.MODELS_DIR)

        # Vector store auto-ingest if empty
        store = get_vector_store()
        if store.count() == 0:
            logger.info("Vector store empty, auto-ingesting manuals")
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                count = await loop.run_in_executor(None, lambda: ingest_manuals("./data/manuals", reset=False))
                logger.info(f"Auto-ingested {count} chunks")
            except Exception as e:
                logger.warning(f"Auto-ingest failed: {e}")

        # Setup simulator and consumer
        mem_q = get_memory_queue()
        self.simulator = StreamSimulator(rate_hz=self.settings.SIM_RATE_HZ, memory_queue=mem_q)
        self.simulator.load_data()

        self.consumer = StreamConsumer(pipeline_callback=self.process_reading, memory_queue=mem_q)

        await self.consumer.start()

        if self.settings.AUTO_START_STREAM:
            await self.start_stream()

    async def _train_models_simple(self) -> None:
        """Train with synthetic data fallback (small defaults) if no saved models."""
        try:
            from scripts.train_models import train_all
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: train_all(models_dir=self.settings.MODELS_DIR, use_synthetic=True))
            # reload
            self.anomaly_model.load(self.settings.MODELS_DIR)
            self.rul_model.load(self.settings.MODELS_DIR)
            self.defect_model.load(self.settings.MODELS_DIR)
        except Exception as e:
            logger.warning(f"Auto-train failed: {e}")

    async def start_stream(self) -> None:
        if not self.simulator:
            logger.warning("Simulator not initialized")
            return
        if self._sim_task and not self._sim_task.done():
            logger.info("Stream already running")
            return
        self._sim_task = asyncio.create_task(self.simulator.run_async())
        logger.info("Stream started")

    async def stop_stream(self) -> None:
        if self.simulator:
            self.simulator.stop()
        if self._sim_task:
            self._sim_task.cancel()
            try:
                await self._sim_task
            except asyncio.CancelledError:
                pass
            self._sim_task = None
        logger.info("Stream stopped")

    def pause_stream(self) -> None:
        if self.simulator:
            self.simulator.pause()

    def resume_stream(self) -> None:
        if self.simulator:
            self.simulator.resume()

    def inject_fault_sync(self, machine_id: str, fault_type: str, magnitude: float, duration_ticks: int, sensors: Optional[list] = None) -> None:
        """Synchronous injection without event publish (for use in async route)."""
        if self.simulator:
            self.simulator.inject(machine_id, fault_type, magnitude, duration_ticks, sensors)

    def inject_fault(self, machine_id: str, fault_type: str, magnitude: float, duration_ticks: int, sensors: Optional[list] = None) -> None:
        if self.simulator:
            self.simulator.inject(machine_id, fault_type, magnitude, duration_ticks, sensors)
        # publish event - handle both async and sync contexts
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.event_bus.publish("fault_injected", {
                "machine_id": machine_id,
                "fault_type": fault_type,
                "magnitude": magnitude,
                "duration_ticks": duration_ticks,
                "sensors": sensors,
            }))
        except RuntimeError:
            # No running loop, try to publish synchronously via new loop or ignore
            logger.info(f"Fault injected {machine_id} {fault_type} but no event loop for publish")

    async def reset(self) -> None:
        """Clears runtime state for fresh demo."""
        self.alert_builder.reset()
        self.feature_extractor.reset()
        self.ring_buffer.clear()
        self.cleaner.reset()
        if self.simulator:
            self.simulator.reset()
        self._impact_metrics = {
            "downtime_avoided": 0.0,
            "defects_prevented": 0,
            "energy_saved": 0.0,
            "alerts_by_severity": {},
            "auto_resolved": 0,
            "human_approved": 0,
        }
        self._total_diagnosis_time_ms = 0
        self._diagnosis_count = 0
        # clear DB? Not full DB, just in-memory? Spec says clears runtime state. We'll keep DB but reset counters
        await self.event_bus.publish("reset", {"message": "pipeline reset"})
        logger.info("Pipeline reset")

    async def process_reading(self, reading: SensorReading) -> None:
        """Per reading: clean -> store -> update ring buffer -> extract features -> run detection -> if alert built, persist and run agent graph."""
        try:
            # clean
            cleaned = self.cleaner.clean(reading)
            if cleaned is None:
                # duplicate
                return
            reading = cleaned

            # store to DB and ring buffer
            # DB store in threadpool
            import asyncio
            loop = asyncio.get_event_loop()

            def _save():
                session = get_db()
                try:
                    save_reading(session, reading)
                finally:
                    session.close()

            await loop.run_in_executor(None, _save)

            self.ring_buffer.add(reading)

            # publish reading event
            await self.event_bus.publish("reading", {
                "machine_id": reading.machine_id,
                "machine_type": reading.machine_type,
                "ts": reading.ts.isoformat(),
                "sequence": reading.sequence,
                "sensors": {k: v for k, v in list(reading.sensors.items())[:10]},  # truncated for perf
            })

            # update machine health? compute later via API route; but emit health_update periodically
            # feature extraction
            self.feature_extractor.add_reading(reading)
            features, top_moving = self.feature_extractor.extract(reading.machine_id)

            # detection
            anomaly_score, anomaly_contrib = (None, [])
            predicted_rul, rul_conf = (None, None)
            defect_prob, defect_conf = (None, None)

            # run models in threadpool (sklearn blocking)
            def _detect():
                a_score, a_contrib = (None, [])
                p_rul, p_conf = (None, None)
                d_prob, d_conf = (None, None)
                # anomaly per machine_type
                if reading.machine_type in self.anomaly_model.models:
                    try:
                        s, contrib = self.anomaly_model.score(reading.machine_type, features)
                        a_score = s
                        a_contrib = contrib
                    except Exception as e:
                        logger.warning(f"Anomaly detect failed: {e}")
                # RUL for turbofan
                if reading.machine_type == "turbofan" and self.rul_model.model is not None:
                    try:
                        rul, conf = self.rul_model.predict_rul(features)
                        p_rul = rul
                        p_conf = conf
                    except Exception as e:
                        logger.warning(f"RUL detect failed: {e}")
                # Defect for bosch
                if reading.machine_type == "bosch" and self.defect_model.model is not None:
                    try:
                        prob, conf = self.defect_model.predict_defect(features)
                        d_prob = prob
                        d_conf = conf
                    except Exception as e:
                        logger.warning(f"Defect detect failed: {e}")
                return a_score, a_contrib, p_rul, p_conf, d_prob, d_conf

            anomaly_score, anomaly_contrib, predicted_rul, rul_conf, defect_prob, defect_conf = await loop.run_in_executor(None, _detect)

            # combine top sensors: prefer anomaly contrib but also top_moving
            combined_top = anomaly_contrib if anomaly_contrib else top_moving
            # if both, merge
            if anomaly_contrib and top_moving:
                # merge by name, keep max deviation
                merged_dict = {}
                for item in anomaly_contrib + top_moving:
                    name = item.get("name")
                    if name not in merged_dict or abs(item.get("deviation", 0)) > abs(merged_dict[name].get("deviation", 0)):
                        merged_dict[name] = item
                combined_top = sorted(merged_dict.values(), key=lambda x: abs(x.get("deviation", 0)), reverse=True)[:10]

            # Determine confidence for alert builder
            confidence = 0.0
            if anomaly_score is not None:
                confidence = max(confidence, anomaly_score)
            if rul_conf is not None and predicted_rul is not None:
                # if RUL low, confidence high
                if predicted_rul < 50:
                    confidence = max(confidence, rul_conf)
            if defect_conf is not None and defect_prob is not None:
                if defect_prob > 0.5:
                    confidence = max(confidence, defect_conf)

            # Build alert
            alert = self.alert_builder.build(
                reading=reading,
                anomaly_score=anomaly_score,
                predicted_rul=predicted_rul,
                defect_prob=defect_prob,
                top_sensors=combined_top,
                feature_snapshot=features,
                confidence_override=confidence if confidence > 0 else None,
            )

            if alert:
                # persist alert
                def _save_alert():
                    session = get_db()
                    try:
                        save_alert(session, alert)
                    finally:
                        session.close()

                await loop.run_in_executor(None, _save_alert)

                # update impact metrics severity count
                sev = alert["severity"]
                self._impact_metrics["alerts_by_severity"][sev] = self._impact_metrics["alerts_by_severity"].get(sev, 0) + 1

                await self.event_bus.publish("alert_created", {
                    "alert_id": alert["alert_id"],
                    "machine_id": alert["machine_id"],
                    "severity": sev,
                    "alert_type": alert["alert_type"],
                })

                # Run agent graph as background task, limited by semaphore
                asyncio.create_task(self._run_agent_graph(alert))

        except Exception as e:
            logger.exception(f"Pipeline process_reading failed for {reading.machine_id}: {e}")

    async def _run_agent_graph(self, alert: Dict[str, Any]) -> None:
        async with self._semaphore:
            try:
                # Build machine context: recent readings summary, last N alerts, etc.
                # For simplicity, fetch recent alerts from DB and ring buffer count
                from storage.db import get_db
                from storage.repositories import list_alerts, get_machine
                import json

                def _get_context():
                    session = get_db()
                    try:
                        m = get_machine(session, alert["machine_id"])
                        recent_alerts = list_alerts(session, machine_id=alert["machine_id"], limit=5)
                        return m, recent_alerts
                    finally:
                        session.close()

                loop = asyncio.get_event_loop()
                machine_orm, recent_alerts = await loop.run_in_executor(None, _get_context)

                machine_context = {
                    "machine_id": alert["machine_id"],
                    "machine_type": alert["machine_type"],
                    "recent_readings_count": self.ring_buffer.count(alert["machine_id"]),
                    "last_alerts": [{"alert_id": a.id, "type": a.alert_type, "severity": a.severity} for a in recent_alerts],
                    "health_score": machine_orm.health_score if machine_orm else 100.0,
                    "status": machine_orm.status if machine_orm else "healthy",
                }

                # Run graph
                start_diag = asyncio.get_event_loop().time()
                final_state = await run_alert(alert, machine_context)
                end_diag = asyncio.get_event_loop().time()
                duration_ms = int((end_diag - start_diag) * 1000)
                self._total_diagnosis_time_ms += duration_ms
                self._diagnosis_count += 1

                # Publish agent steps as they happen from trace
                for trace_event in final_state.get("trace", []):
                    await self.event_bus.publish("agent_step", trace_event)

                # Publish diagnosis_ready, plan_ready
                if final_state.get("diagnosis"):
                    await self.event_bus.publish("diagnosis_ready", {
                        "alert_id": alert["alert_id"],
                        "diagnosis": final_state["diagnosis"],
                        "citations": final_state.get("citations_formatted", []),
                    })

                if final_state.get("plan"):
                    await self.event_bus.publish("plan_ready", {
                        "alert_id": alert["alert_id"],
                        "plan": final_state["plan"],
                    })
                    # update impact metrics
                    est = final_state["plan"].get("estimated_impact", {})
                    self._impact_metrics["downtime_avoided"] += float(est.get("downtime_avoided_minutes", 0))
                    self._impact_metrics["defects_prevented"] += int(est.get("defects_prevented", 0))
                    self._impact_metrics["energy_saved"] += float(est.get("energy_saved_kwh", 0))

                # Ticketing and approval
                action_out = final_state.get("action_output", {})
                ticket_id = action_out.get("ticket_id")
                ticket_status = action_out.get("ticket_status", "open")
                plan = final_state.get("plan", {})

                if ticket_id:
                    # Create ticket in DB
                    def _create_ticket():
                        create_ticket(
                            ticket_id=ticket_id,
                            alert_id=alert["alert_id"],
                            machine_id=alert["machine_id"],
                            title=f"{alert['alert_type']} on {alert['machine_id']} - {plan.get('action_type', 'maintenance')}",
                            description=f"Root cause: {final_state.get('diagnosis', {}).get('root_cause', 'unknown')}. Reasoning: {final_state.get('diagnosis', {}).get('reasoning', '')[:500]}",
                            priority=alert["severity"],
                            status=ticket_status,
                            instructions=action_out.get("repair_instructions", ""),
                        )
                        # Save traces
                        session = get_db()
                        try:
                            for te in final_state.get("trace", []):
                                save_trace(session, alert["alert_id"], te, final_state)
                        finally:
                            session.close()

                        # Approval if needed
                        if plan.get("requires_approval"):
                            create_approval_request(alert["alert_id"], ticket_id)
                        # If needs_human_review
                        if ticket_status == "needs_human_review":
                            # create approval with needs_human_review status? Actually ticket status already
                            pass

                    await loop.run_in_executor(None, _create_ticket)

                    await self.event_bus.publish("ticket_updated", {
                        "ticket_id": ticket_id,
                        "alert_id": alert["alert_id"],
                        "status": ticket_status,
                    })

                    if plan.get("requires_approval"):
                        await self.event_bus.publish("approval_required", {
                            "alert_id": alert["alert_id"],
                            "ticket_id": ticket_id,
                            "action_type": plan.get("action_type"),
                            "risk_level": plan.get("risk_level"),
                        })
                        self._impact_metrics["human_approved"] += 1
                    else:
                        self._impact_metrics["auto_resolved"] += 1

                    # Notifier
                    try:
                        await loop.run_in_executor(None, lambda: notify_event("ticket_created", {
                            "ticket_id": ticket_id,
                            "alert_id": alert["alert_id"],
                            "machine_id": alert["machine_id"],
                            "action_type": plan.get("action_type"),
                        }))
                    except Exception:
                        pass

                # Also publish final decision trace ready
                await self.event_bus.publish("decision_ready", {
                    "alert_id": alert["alert_id"],
                    "final_state": {k: v for k, v in final_state.items() if k not in ("evidence",)},  # don't send huge evidence
                })

            except Exception as e:
                logger.exception(f"Agent graph run failed for alert {alert.get('alert_id')}: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        mean_time = (self._total_diagnosis_time_ms / self._diagnosis_count) if self._diagnosis_count else 0
        return {
            "downtime_avoided_minutes": self._impact_metrics["downtime_avoided"],
            "defects_prevented": self._impact_metrics["defects_prevented"],
            "energy_saved_kwh": self._impact_metrics["energy_saved"],
            "alerts_by_severity": self._impact_metrics["alerts_by_severity"],
            "mean_time_to_diagnose_ms": mean_time,
            "auto_resolved_count": self._impact_metrics["auto_resolved"],
            "human_approved_count": self._impact_metrics["human_approved"],
            "total_diagnoses": self._diagnosis_count,
        }

    async def shutdown(self) -> None:
        await self.stop_stream()
        if self.consumer:
            await self.consumer.stop()
        logger.info("Pipeline shutdown")


# Singleton
_global_pipeline: Optional[Pipeline] = None


def get_pipeline() -> Pipeline:
    global _global_pipeline
    if _global_pipeline is None:
        _global_pipeline = Pipeline()
    return _global_pipeline
