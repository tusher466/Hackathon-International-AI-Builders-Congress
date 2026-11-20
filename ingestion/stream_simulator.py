"""Stream simulator: loads datasets or synthetic fallback, publishes readings."""
from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading

import numpy as np
import pandas as pd

from config.settings import get_settings
from ingestion.schemas import SensorReading

logger = logging.getLogger(__name__)


class FaultInjector:
    """Handles injected faults."""

    def __init__(self):
        # machine_id -> list of active faults
        self.active_faults: Dict[str, List[Dict[str, Any]]] = {}

    def inject(self, machine_id: str, fault_type: str, magnitude: float, duration_ticks: int, sensors: Optional[List[str]] = None) -> None:
        fault = {
            "type": fault_type,
            "magnitude": magnitude,
            "duration": duration_ticks,
            "remaining": duration_ticks,
            "sensors": sensors,
            "start_ts": datetime.now(timezone.utc),
        }
        self.active_faults.setdefault(machine_id, []).append(fault)
        logger.info(f"Injected fault {fault_type} on {machine_id} magnitude={magnitude} duration={duration_ticks}")

    def apply(self, reading: SensorReading) -> SensorReading:
        faults = self.active_faults.get(reading.machine_id, [])
        if not faults:
            return reading

        new_sensors = dict(reading.sensors)
        remaining_faults = []
        for f in faults:
            if f["remaining"] <= 0:
                continue
            ftype = f["type"]
            mag = f["magnitude"]
            target_sensors = f["sensors"] or list(new_sensors.keys())[:5]  # default first 5

            if ftype == "drift":
                # gradual ramp: increase each tick by mag/duration
                ramp = mag * (1 - f["remaining"] / f["duration"]) if f["duration"] > 0 else mag
                for s in target_sensors:
                    if s in new_sensors and new_sensors[s] is not None:
                        new_sensors[s] = new_sensors[s] + ramp

            elif ftype == "spike":
                for s in target_sensors:
                    if s in new_sensors and new_sensors[s] is not None:
                        new_sensors[s] = new_sensors[s] + mag * random.choice([-1, 1]) * 5

            elif ftype == "stuck":
                # freeze sensor to last value + mag? For simplicity set to constant
                for s in target_sensors:
                    if s in new_sensors:
                        new_sensors[s] = mag

            elif ftype == "degradation":
                # accelerated wear: for turbofan, decrease sensor efficiency, increase temps
                for s in target_sensors:
                    if s in new_sensors and new_sensors[s] is not None:
                        # degrade by adding magnitude scaled by elapsed
                        elapsed = f["duration"] - f["remaining"]
                        new_sensors[s] = new_sensors[s] + mag * elapsed * 0.1

            elif ftype == "defect_burst":
                for s in target_sensors:
                    if s in new_sensors and new_sensors[s] is not None:
                        new_sensors[s] = new_sensors[s] * (1 + mag)

            f["remaining"] -= 1
            if f["remaining"] > 0:
                remaining_faults.append(f)
            else:
                logger.info(f"Fault expired on {reading.machine_id}: {ftype}")

        self.active_faults[reading.machine_id] = remaining_faults
        reading.sensors = new_sensors
        # mark meta
        if faults:
            reading.meta["injected_fault"] = faults[0]["type"]
        return reading

    def clear(self, machine_id: Optional[str] = None) -> None:
        if machine_id:
            self.active_faults.pop(machine_id, None)
        else:
            self.active_faults.clear()


def _synthetic_secom(n_rows: int = 1567, n_sensors: int = 590) -> pd.DataFrame:
    logger.warning("SECOM data missing, generating synthetic equivalent")
    np.random.seed(0)
    data = np.random.normal(0, 1, (n_rows, n_sensors))
    # inject some failures
    labels = np.random.choice([-1, 1], size=n_rows, p=[0.93, 0.07])
    df = pd.DataFrame(data, columns=[f"s{i}" for i in range(n_sensors)])
    df_labels = pd.DataFrame({"label": labels, "ts": pd.date_range("2023-01-01", periods=n_rows, freq="min")})
    return df, df_labels


def _synthetic_cmapss(n_units: int = 5, cycles_per_unit: int = 200) -> Dict[str, pd.DataFrame]:
    logger.warning("CMAPSS data missing, generating synthetic")
    np.random.seed(1)
    result = {}
    for unit in range(1, n_units + 1):
        cycles = cycles_per_unit - random.randint(0, 50)
        data = []
        for cyc in range(1, cycles + 1):
            op_settings = np.random.uniform(0, 1, 3)
            sensors = np.random.normal(0, 1, 21)
            # Simulate degradation: sensors drift as cycle increases
            drift = (cyc / cycles) * np.random.normal(0.5, 0.1, 21)
            sensors = sensors + drift
            row = [unit, cyc] + list(op_settings) + list(sensors)
            data.append(row)
        columns = ["unit", "cycle", "op_setting_1", "op_setting_2", "op_setting_3"] + [f"s{i}" for i in range(1, 22)]
        result[f"TURBO-{unit:02d}"] = pd.DataFrame(data, columns=columns)
    return result


def _synthetic_bosch(n_rows: int = 1000, n_sensors: int = 100) -> pd.DataFrame:
    logger.warning("Bosch data missing, generating synthetic")
    np.random.seed(2)
    data = np.random.normal(0, 1, (n_rows, n_sensors))
    # defects 3%
    response = np.random.choice([0, 1], size=n_rows, p=[0.97, 0.03])
    df = pd.DataFrame(data, columns=[f"L1_S{s}_F0" for s in range(n_sensors)])
    df["Response"] = response
    return df


class StreamSimulator:
    """Loads datasets, interleaves, publishes readings."""

    def __init__(
        self,
        rate_hz: float = 2.0,
        loop: bool = True,
        memory_queue: Optional[asyncio.Queue] = None,
        mqtt_client: Optional[Any] = None,
    ):
        self.settings = get_settings()
        self.rate_hz = rate_hz
        self.loop = loop
        self.memory_queue = memory_queue
        self.mqtt_client = mqtt_client
        self.fault_injector = FaultInjector()
        self._running = False
        self._paused = False
        self._thread: Optional[threading.Thread] = None
        self._sequence_counters: Dict[str, int] = {}
        self._datasets_loaded = False

        # Data holders
        self.secom_data: Optional[pd.DataFrame] = None
        self.secom_labels: Optional[pd.DataFrame] = None
        self.cmapss_data: Dict[str, pd.DataFrame] = {}
        self.bosch_data: Optional[pd.DataFrame] = None

        # iterators
        self._secom_idx = 0
        self._cmapss_indices: Dict[str, int] = {}
        self._bosch_idx = 0
        self._machine_list: List[str] = []

    def load_data(self) -> None:
        raw_path = Path("./data/raw")
        # SECOM
        try:
            secom_data_path = raw_path / "secom.data"
            secom_labels_path = raw_path / "secom_labels.data"
            if secom_data_path.exists() and secom_labels_path.exists():
                self.secom_data = pd.read_csv(secom_data_path, sep=" ", header=None)
                self.secom_data.columns = [f"s{i}" for i in range(self.secom_data.shape[1])]
                lbl = pd.read_csv(secom_labels_path, sep=" ", header=None)
                lbl.columns = ["label", "timestamp"] if lbl.shape[1] == 2 else ["label"]
                if "timestamp" not in lbl.columns:
                    lbl["timestamp"] = pd.date_range("2023-01-01", periods=len(lbl), freq="min")
                self.secom_labels = lbl
                logger.info(f"Loaded SECOM: {self.secom_data.shape}")
            else:
                self.secom_data, self.secom_labels = _synthetic_secom()
        except Exception as e:
            logger.warning(f"SECOM load failed {e}, using synthetic")
            self.secom_data, self.secom_labels = _synthetic_secom()

        # CMAPSS
        try:
            cmapss_path = raw_path / "train_FD001.txt"
            if cmapss_path.exists():
                columns = ["unit", "cycle", "op_setting_1", "op_setting_2", "op_setting_3"] + [f"s{i}" for i in range(1, 22)]
                # FD001 file has 26 columns space separated
                df = pd.read_csv(cmapss_path, sep="\s+", header=None)
                # if more columns, trim
                df = df.iloc[:, :len(columns)]
                df.columns = columns[: df.shape[1]]
                # map first 5 units to TURBO machines
                for unit in sorted(df["unit"].unique())[:5]:
                    mid = f"TURBO-{int(unit):02d}"
                    self.cmapss_data[mid] = df[df["unit"] == unit].copy()
                logger.info(f"Loaded CMAPSS for {len(self.cmapss_data)} units")
            else:
                self.cmapss_data = _synthetic_cmapss()
        except Exception as e:
            logger.warning(f"CMAPSS load failed {e}, synthetic")
            self.cmapss_data = _synthetic_cmapss()

        # Bosch
        try:
            bosch_path = raw_path / "train_numeric.csv"
            if bosch_path.exists():
                # load first N rows, maybe sample
                self.bosch_data = pd.read_csv(bosch_path, nrows=2000)
                logger.info(f"Loaded Bosch: {self.bosch_data.shape}")
            else:
                self.bosch_data = _synthetic_bosch()
        except Exception as e:
            logger.warning(f"Bosch load failed {e}, synthetic")
            self.bosch_data = _synthetic_bosch()

        # machine list
        self._machine_list = ["SECOM-01", "BOSCH-L1"] + list(self.cmapss_data.keys())
        # init sequence counters
        for mid in self._machine_list:
            self._sequence_counters[mid] = 0
            self._cmapss_indices[mid] = 0
        self._datasets_loaded = True

    def _get_next_reading_for_machine(self, machine_id: str) -> Optional[SensorReading]:
        seq = self._sequence_counters.get(machine_id, 0)
        ts = datetime.now(timezone.utc)
        # ensure increasing ts slightly
        sensors: Dict[str, float] = {}
        meta: Dict[str, Any] = {}
        mtype = "secom"
        if machine_id.startswith("SECOM"):
            mtype = "secom"
            if self.secom_data is not None:
                idx = self._secom_idx % len(self.secom_data)
                row = self.secom_data.iloc[idx]
                sensors = {k: float(v) for k, v in row.to_dict().items() if pd.notna(v)}
                if self.secom_labels is not None:
                    lbl_row = self.secom_labels.iloc[idx]
                    meta["ground_truth_label"] = int(lbl_row["label"]) if "label" in lbl_row else 0
                # increment secom idx only when this machine is chosen
                self._secom_idx += 1
            else:
                sensors = {f"s{i}": float(np.random.normal()) for i in range(10)}
        elif machine_id.startswith("TURBO"):
            mtype = "turbofan"
            df = self.cmapss_data.get(machine_id)
            if df is not None and len(df) > 0:
                idx = self._cmapss_indices.get(machine_id, 0) % len(df)
                row = df.iloc[idx]
                # sensors s1..s21 + op_settings
                sensors = {}
                for c in df.columns:
                    if c.startswith("s") or c.startswith("op_"):
                        sensors[c] = float(row[c])
                meta["unit"] = int(row["unit"])
                meta["cycle"] = int(row["cycle"])
                meta["op_settings"] = {f"op_setting_{i}": float(row[f"op_setting_{i}"]) for i in range(1, 4) if f"op_setting_{i}" in row}
                # RUL label
                max_cycle = df["cycle"].max()
                meta["RUL"] = int(max_cycle - row["cycle"])
                self._cmapss_indices[machine_id] = (idx + 1) % len(df)
            else:
                sensors = {f"s{i}": float(np.random.normal()) for i in range(1, 22)}
        elif machine_id.startswith("BOSCH"):
            mtype = "bosch"
            if self.bosch_data is not None:
                idx = self._bosch_idx % len(self.bosch_data)
                row = self.bosch_data.iloc[idx]
                sensors = {}
                for col, val in row.items():
                    if col == "Response":
                        meta["ground_truth_defect"] = int(val)
                    else:
                        try:
                            sensors[col] = float(val) if pd.notna(val) else 0.0
                        except Exception:
                            pass
                self._bosch_idx += 1
                # limit sensors to first 100 for efficiency
                if len(sensors) > 100:
                    sensors = dict(list(sensors.items())[:100])
            else:
                sensors = {f"L1_S{i}_F0": float(np.random.normal()) for i in range(20)}

        reading = SensorReading(
            machine_id=machine_id,
            machine_type=mtype,  # type: ignore
            ts=ts,
            sequence=seq,
            sensors=sensors,
            meta=meta,
        )
        self._sequence_counters[machine_id] = seq + 1
        # apply fault injection
        reading = self.fault_injector.apply(reading)
        return reading

    def get_next_reading_round_robin(self) -> Optional[SensorReading]:
        if not self._machine_list:
            return None
        # choose machine in round-robin
        # we maintain an internal pointer
        if not hasattr(self, "_rr_idx"):
            self._rr_idx = 0
        machine_id = self._machine_list[self._rr_idx % len(self._machine_list)]
        self._rr_idx += 1
        return self._get_next_reading_for_machine(machine_id)

    async def publish_reading(self, reading: SensorReading) -> None:
        payload = reading.model_dump_json()
        # MQTT publish if configured
        if self.settings.STREAM_BACKEND == "mqtt" and self.mqtt_client:
            try:
                topic = f"{self.settings.MQTT_TOPIC_PREFIX}/{reading.machine_id}/readings"
                self.mqtt_client.publish(topic, payload)
            except Exception as e:
                logger.warning(f"MQTT publish failed: {e}")
        # memory queue
        if self.memory_queue is not None:
            try:
                # non-blocking try
                self.memory_queue.put_nowait(payload)
            except asyncio.QueueFull:
                logger.warning("Memory queue full, dropping reading")

    async def run_async(self) -> None:
        """Async infinite loop for simulator."""
        self._running = True
        if not self._datasets_loaded:
            self.load_data()
        logger.info(f"Stream simulator starting rate={self.rate_hz}Hz machines={self._machine_list}")
        while self._running:
            if self._paused:
                await asyncio.sleep(0.1)
                continue
            reading = self.get_next_reading_round_robin()
            if reading:
                await self.publish_reading(reading)
            await asyncio.sleep(1.0 / max(self.rate_hz, 0.1))

    def run_in_thread(self) -> None:
        """Synchronous wrapper that runs publish via thread (for non-async contexts)."""
        # This uses asyncio.run in new loop
        asyncio.run(self.run_async())

    # Control methods
    def start(self) -> None:
        if self._running:
            return
        self._running = True
        # start background thread if needed for non-async usage
        # but for FastAPI we use async task
        logger.info("Simulator start called")

    def stop(self) -> None:
        self._running = False
        logger.info("Simulator stopped")

    def pause(self) -> None:
        self._paused = True
        logger.info("Simulator paused")

    def resume(self) -> None:
        self._paused = False
        logger.info("Simulator resumed")

    def inject(self, machine_id: str, fault_type: str, magnitude: float, duration_ticks: int, sensors: Optional[List[str]] = None) -> None:
        self.fault_injector.inject(machine_id, fault_type, magnitude, duration_ticks, sensors)

    def reset(self) -> None:
        self._secom_idx = 0
        self._bosch_idx = 0
        for k in self._cmapss_indices:
            self._cmapss_indices[k] = 0
        for k in self._sequence_counters:
            self._sequence_counters[k] = 0
        self.fault_injector.clear()
        logger.info("Simulator reset")

    # CLI entry
    @staticmethod
    def cli_demo() -> None:
        sim = StreamSimulator(rate_hz=1.0)
        sim.load_data()
        for _ in range(10):
            r = sim.get_next_reading_round_robin()
            print(r.model_dump_json()[:200])


# Global memory queue singleton for fallback
_memory_queue: Optional[asyncio.Queue] = None


def get_memory_queue() -> asyncio.Queue:
    global _memory_queue
    if _memory_queue is None:
        _memory_queue = asyncio.Queue(maxsize=10000)
    return _memory_queue
