"""Alert severity and cooldown tests."""
from datetime import datetime, timezone
from ingestion.schemas import SensorReading
from detection.alert_builder import AlertBuilder


def test_alert_severity_rules():
    builder = AlertBuilder()
    reading = SensorReading(
        machine_id="TURBO-01",
        machine_type="turbofan",
        ts=datetime.now(timezone.utc),
        sequence=0,
        sensors={},
        meta={},
    )
    # Critical anomaly
    alert = builder.build(reading, anomaly_score=0.9, predicted_rul=None, defect_prob=None, top_sensors=[], feature_snapshot={})
    assert alert is not None
    assert alert["severity"] == "critical"
    assert alert["alert_type"] == "anomaly"

    # Should be suppressed by cooldown immediately after
    alert2 = builder.build(reading, anomaly_score=0.9, predicted_rul=None, defect_prob=None, top_sensors=[], feature_snapshot={})
    assert alert2 is None  # cooldown

    # Reset and test RUL critical
    builder.reset()
    alert_rul = builder.build(reading, anomaly_score=None, predicted_rul=15, defect_prob=None, top_sensors=[], feature_snapshot={})
    assert alert_rul is not None
    assert alert_rul["alert_type"] == "degradation"
    assert alert_rul["severity"] == "critical"


def test_alert_cooldown():
    builder = AlertBuilder()
    reading = SensorReading(
        machine_id="SECOM-01",
        machine_type="secom",
        ts=datetime.now(timezone.utc),
        sequence=0,
        sensors={},
        meta={},
    )
    alert = builder.build(reading, anomaly_score=0.8, predicted_rul=None, defect_prob=None, top_sensors=[], feature_snapshot={})
    assert alert is not None

    # Next 9 readings should be suppressed (cooldown 10)
    for _ in range(9):
        a = builder.build(reading, anomaly_score=0.8, predicted_rul=None, defect_prob=None, top_sensors=[], feature_snapshot={})
        assert a is None

    # After cooldown, should allow again
    # Need 1 more to expire
    a = builder.build(reading, anomaly_score=0.8, predicted_rul=None, defect_prob=None, top_sensors=[], feature_snapshot={})
    assert a is not None


def test_defect_alert():
    builder = AlertBuilder()
    reading = SensorReading(
        machine_id="BOSCH-L1",
        machine_type="bosch",
        ts=datetime.now(timezone.utc),
        sequence=0,
        sensors={},
        meta={},
    )
    alert = builder.build(reading, anomaly_score=None, predicted_rul=None, defect_prob=0.9, top_sensors=[], feature_snapshot={})
    assert alert["alert_type"] == "defect_risk"
    assert alert["severity"] == "critical"
