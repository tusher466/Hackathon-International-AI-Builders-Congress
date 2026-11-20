"""Schema validation tests."""
import pytest
from ingestion.schemas import SensorReading
from datetime import datetime, timezone


def test_sensor_reading_valid():
    reading = SensorReading(
        machine_id="SECOM-01",
        machine_type="secom",
        ts=datetime.now(timezone.utc),
        sequence=0,
        sensors={"s0": 1.0, "s1": None},
        meta={},
    )
    assert reading.machine_id == "SECOM-01"
    assert reading.sensors["s1"] is None


def test_sensor_reading_invalid_machine_type():
    with pytest.raises(Exception):
        SensorReading(
            machine_id="X-01",
            machine_type="invalid",  # type: ignore
            ts=datetime.now(timezone.utc),
            sequence=0,
            sensors={},
        )


def test_sensor_reading_from_json():
    reading = SensorReading(
        machine_id="TURBO-01",
        machine_type="turbofan",
        ts=datetime.now(timezone.utc),
        sequence=5,
        sensors={"s1": 0.5},
        meta={"RUL": 100},
    )
    payload = reading.model_dump_json()
    restored = SensorReading.model_validate_json(payload)
    assert restored.machine_id == reading.machine_id
    assert restored.sensors["s1"] == 0.5
