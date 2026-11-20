"""Feature extractor shape tests."""
from ingestion.feature_extractor import FeatureExtractor
from ingestion.schemas import SensorReading
from datetime import datetime, timezone


def test_feature_extractor_output_shape():
    extractor = FeatureExtractor(window_size=5)
    # Add 5 readings
    for i in range(5):
        reading = SensorReading(
            machine_id="SECOM-01",
            machine_type="secom",
            ts=datetime.now(timezone.utc),
            sequence=i,
            sensors={"s0": float(i), "s1": float(i*2)},
            meta={},
        )
        extractor.add_reading(reading)

    assert extractor.window_full("SECOM-01") is True
    features, top_moving = extractor.extract("SECOM-01")
    # Each sensor should have mean, std, min, max, slope, roc, zscore, spike
    assert "s0_mean" in features
    assert "s1_mean" in features
    assert len(top_moving) > 0
    assert "name" in top_moving[0]
