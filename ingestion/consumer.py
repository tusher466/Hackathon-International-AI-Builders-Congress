"""Consumer for MQTT or in-memory queue."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Callable, Optional, Any

from config.settings import get_settings
from ingestion.schemas import SensorReading

logger = logging.getLogger(__name__)


class StreamConsumer:
    """Subscribes to factory/+/readings (MQTT) or in-memory queue."""

    def __init__(
        self,
        pipeline_callback: Callable[[SensorReading], Any],
        memory_queue: Optional[asyncio.Queue] = None,
        mqtt_client: Optional[Any] = None,
    ):
        self.settings = get_settings()
        self.pipeline_callback = pipeline_callback
        self.memory_queue = memory_queue
        self.mqtt_client = mqtt_client
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.dead_letter: list[str] = []

    async def start(self) -> None:
        self._running = True
        if self.settings.STREAM_BACKEND == "mqtt":
            self._start_mqtt()
        # Always start memory queue consumer as fallback / primary if memory mode
        self._task = asyncio.create_task(self._consume_memory_loop())
        logger.info(f"Consumer started backend={self.settings.STREAM_BACKEND}")

    def _start_mqtt(self) -> None:
        try:
            import paho.mqtt.client as mqtt

            client = mqtt.Client(client_id=self.settings.MQTT_CLIENT_ID + "_consumer")
            client.on_connect = self._on_mqtt_connect
            client.on_message = self._on_mqtt_message
            client.on_disconnect = self._on_mqtt_disconnect

            client.connect(self.settings.MQTT_HOST, self.settings.MQTT_PORT, 60)
            client.loop_start()
            self.mqtt_client = client
            logger.info("MQTT consumer connected")
        except Exception as e:
            logger.warning(f"MQTT consumer init failed, falling back to memory: {e}")

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        topic = f"{self.settings.MQTT_TOPIC_PREFIX}/+/readings"
        client.subscribe(topic)
        logger.info(f"MQTT subscribed to {topic}")

    def _on_mqtt_disconnect(self, client, userdata, rc):
        logger.warning(f"MQTT disconnected rc={rc}, will attempt reconnect with backoff")
        # paho handles reconnect if loop_start used

    def _on_mqtt_message(self, client, userdata, msg):
        payload = msg.payload
        try:
            reading = SensorReading.from_mqtt_payload(payload)
            # schedule callback in event loop if running
            # need to get loop; use asyncio.run_coroutine_threadsafe if possible
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self._handle_reading(reading), loop)
            else:
                # fallback sync
                asyncio.run(self._handle_reading(reading))
        except Exception as e:
            logger.error(f"Malformed MQTT message: {e} payload={payload[:200]}")
            self.dead_letter.append(str(payload[:500]))

    async def _handle_reading(self, reading: SensorReading) -> None:
        try:
            result = self.pipeline_callback(reading)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            logger.exception(f"Pipeline callback failed for {reading.machine_id}: {e}")

    async def _consume_memory_loop(self) -> None:
        if not self.memory_queue:
            # import global queue
            from ingestion.stream_simulator import get_memory_queue
            self.memory_queue = get_memory_queue()

        assert self.memory_queue is not None
        while self._running:
            try:
                # wait with timeout to allow shutdown
                payload = await asyncio.wait_for(self.memory_queue.get(), timeout=1.0)
                try:
                    # payload may be JSON string
                    if isinstance(payload, (bytes, bytearray)):
                        payload = payload.decode("utf-8")
                    if isinstance(payload, str):
                        reading = SensorReading.model_validate_json(payload)
                    elif isinstance(payload, dict):
                        reading = SensorReading.model_validate(payload)
                    else:
                        raise ValueError(f"Unknown payload type {type(payload)}")
                    await self._handle_reading(reading)
                except Exception as e:
                    logger.error(f"Failed to validate memory queue message: {e}")
                    self.dead_letter.append(str(payload)[:500])
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.exception(f"Memory consumer loop error: {e}")
                await asyncio.sleep(0.1)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.mqtt_client:
            try:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            except Exception:
                pass
        logger.info("Consumer stopped")
