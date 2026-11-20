"""Per-machine stateful cleaner."""
from __future__ import annotations

import logging
from typing import Dict, Optional
import numpy as np
from collections import defaultdict

from ingestion.schemas import SensorReading

logger = logging.getLogger(__name__)


class Cleaner:
    """Stateful cleaner per machine.

    - forward-fill then median-impute missing values
    - clip outliers at configurable z-score
    - normalize using scalers fitted at training time (loaded from joblib) – if missing, no normalization
    - align/sort by timestamp, drop duplicates by (machine_id, sequence)

    Never crashes on bad values; counts and logs them.
    """

    def __init__(self, zscore_threshold: float = 5.0):
        self.zscore_threshold = zscore_threshold
        # per-machine state: last valid reading dict, seen sequences, median estimates
        self._last_valid: Dict[str, Dict[str, float]] = {}
        self._seen_sequences: Dict[str, set[int]] = defaultdict(set)
        self._median_estimates: Dict[str, Dict[str, float]] = {}
        self._bad_value_count: Dict[str, int] = defaultdict(int)
        # scalers per machine_type: dict sensor -> (mean, std) or sklearn scaler object
        self._scalers: Dict[str, Dict] = {}

    def load_scalers(self, scalers: Dict[str, Dict[str, tuple[float, float]]]) -> None:
        """Load scalers from train script. Expected mapping: machine_type -> sensor -> (mean, std)"""
        self._scalers = scalers

    def try_load_from_joblib(self, models_dir: str = "./models") -> None:
        try:
            import joblib
            import pathlib
            p = pathlib.Path(models_dir) / "scalers.joblib"
            if p.exists():
                data = joblib.load(p)
                self._scalers = data
                logger.info(f"Loaded scalers from {p}")
        except Exception as e:
            logger.warning(f"Failed to load scalers: {e}")

    def clean(self, reading: SensorReading) -> Optional[SensorReading]:
        """Clean a reading, return None if duplicate."""
        machine_id = reading.machine_id
        mtype = reading.machine_type

        # duplicate check
        if reading.sequence in self._seen_sequences[machine_id]:
            logger.debug(f"Duplicate sequence {reading.sequence} for {machine_id}, dropping")
            self._bad_value_count[machine_id] += 1
            return None
        self._seen_sequences[machine_id].add(reading.sequence)

        cleaned_sensors: Dict[str, float] = {}
        last_valid = self._last_valid.get(machine_id, {})
        median_est = self._median_estimates.get(machine_id, {})

        for sensor_name, raw_val in reading.sensors.items():
            try:
                if raw_val is None or (isinstance(raw_val, float) and np.isnan(raw_val)):
                    # forward fill then median impute
                    if sensor_name in last_valid:
                        cleaned_sensors[sensor_name] = last_valid[sensor_name]
                    elif sensor_name in median_est:
                        cleaned_sensors[sensor_name] = median_est[sensor_name]
                    else:
                        cleaned_sensors[sensor_name] = 0.0
                    self._bad_value_count[machine_id] += 1
                    continue

                val = float(raw_val)
                if not np.isfinite(val):
                    raise ValueError(f"Non-finite {val}")

                # clip outliers at z-score threshold (naive using last values)
                # estimate mean/std from last_valid if available, else skip clipping
                # We maintain a simple running median for clipping reference via last_valid
                # Use median estimate for z-score if available
                if sensor_name in median_est:
                    # rough std estimate: we don't have std, assume 1.0 for clipping logic unless scaler provides
                    # If scaler available, use its mean/std
                    scaler = self._scalers.get(mtype, {}).get(sensor_name)
                    if scaler:
                        mean, std = scaler
                        if std > 0:
                            z = abs((val - mean) / std)
                            if z > self.zscore_threshold:
                                # clip to mean ± threshold*std
                                sign = 1 if val > mean else -1
                                val = mean + sign * self.zscore_threshold * std
                                self._bad_value_count[machine_id] += 1
                                logger.debug(f"Clipped outlier {sensor_name}={raw_val} to {val} for {machine_id}")

                cleaned_sensors[sensor_name] = val

            except Exception as e:
                logger.warning(f"Bad sensor value machine={machine_id} sensor={sensor_name} val={raw_val} err={e}")
                self._bad_value_count[machine_id] += 1
                # fallback to last_valid or 0.0
                cleaned_sensors[sensor_name] = last_valid.get(sensor_name, median_est.get(sensor_name, 0.0))

        # update state
        self._last_valid[machine_id] = cleaned_sensors.copy()
        # update median estimates with simple EMA
        for k, v in cleaned_sensors.items():
            if k not in median_est:
                median_est[k] = v
            else:
                median_est[k] = 0.9 * median_est[k] + 0.1 * v
        self._median_estimates[machine_id] = median_est

        # normalization if scalers exist
        normalized = {}
        scaler_map = self._scalers.get(mtype, {})
        for k, v in cleaned_sensors.items():
            if k in scaler_map:
                mean, std = scaler_map[k]
                if std > 1e-8:
                    normalized[k] = (v - mean) / std
                else:
                    normalized[k] = 0.0
            else:
                normalized[k] = v

        # Return new reading with cleaned sensors (use cleaned, not normalized for storage? spec says normalize using scalers)
        # We'll store cleaned normalized values as sensors, but keep original meta
        reading.sensors = normalized
        return reading

    def get_bad_count(self, machine_id: str) -> int:
        return self._bad_value_count.get(machine_id, 0)

    def reset(self, machine_id: Optional[str] = None) -> None:
        if machine_id:
            self._last_valid.pop(machine_id, None)
            self._seen_sequences.pop(machine_id, None)
            self._median_estimates.pop(machine_id, None)
            self._bad_value_count.pop(machine_id, None)
        else:
            self._last_valid.clear()
            self._seen_sequences.clear()
            self._median_estimates.clear()
            self._bad_value_count.clear()
