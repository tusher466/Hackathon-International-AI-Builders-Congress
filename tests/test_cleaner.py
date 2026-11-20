"""Cleaner behavior tests."""
from ingestion.cleaner import Cleaner
from ingestion.schemas import SensorReading
from datetime import datetime, timezone


def test_cleaner_missing_values():
    cleaner = Cleaner()
    reading = SensorReading(
        machine_id="SECOM-01",
        machine_type="secom",
        ts=datetime.now(timezone.utc),
        sequence=0,
        sensors={"s0": None, "s1": 1.0},
        meta={},
    )
    cleaned = cleaner.clean(reading)
    assert cleaned is not None
    # s0 should be imputed to 0.0 first time
    assert cleaned.sensors["s0"] == 0.0
    assert cleaned.sensors["s1"] == 1.0


def test_cleaner_duplicate():
    cleaner = Cleaner()
    reading1 = SensorReading(
        machine_id="TURBO-01",
        machine_type="turbofan",
        ts=datetime.now(timezone.utc),
        sequence=1,
        sensors={"s1": 1.0},
        meta={},
    )
    reading2 = SensorReading(
        machine_id="TURBO-01",
        machine_type="turbofan",
        ts=datetime.now(timezone.utc),
        sequence=1,
        sensors={"s1": 2.0},
        meta={},
    )
    assert cleaner.clean(reading1) is not None
    assert cleaner.clean(reading2) is None  # duplicate


def test_cleaner_outlier_clipping():
    cleaner = Cleaner(zscore_threshold=2.0)
    # Load scalers dummy
    cleaner.load_scalers({"secom": {"s0": (0.0, 1.0)}})
    reading = SensorReading(
        machine_id="SECOM-01",
        machine_type="secom",
        ts=datetime.now(timezone.utc),
        sequence=0,
        sensors={"s0": 100.0},  # outlier
        meta={},
    )
    # First reading no median yet, so no clipping yet? But second will clip
    cleaner.clean(reading)
    reading2 = SensorReading(
        machine_id="SECOM-01",
        machine_type="secom",
        ts=datetime.now(timezone.utc),
        sequence=1,
        sensors={"s0": 100.0},
        meta={},
    )
    cleaned2 = cleaner.clean(reading2)
    # Should be clipped to mean + threshold*std = 0+2*1=2
    assert abs(cleaned2.sensors["s0"]) <= 2.1
