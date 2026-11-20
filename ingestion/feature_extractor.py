"""Feature extractor with sliding window."""
from __future__ import annotations

import logging
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import numpy as np

from ingestion.schemas import SensorReading

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Per-machine sliding window feature extractor.

    For each machine, maintain window of last N readings (default 30).
    Outputs:
    - flat feature dict
    - list of top moving sensors
    For SECOM (590 sensors) reduce dimensionality via variance filtering + PCA if available.
    """

    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self._windows: Dict[str, deque[SensorReading]] = defaultdict(lambda: deque(maxlen=self.window_size))
        self._pca_models: Dict[str, object] = {}  # machine_type -> pca
        self._baseline_means: Dict[str, Dict[str, float]] = {}  # machine_id -> sensor -> mean
        self._baseline_stds: Dict[str, Dict[str, float]] = {}

    def load_pca(self, pca_dict: Dict[str, object]) -> None:
        self._pca_models = pca_dict

    def try_load_from_joblib(self, models_dir: str = "./models") -> None:
        try:
            import joblib
            from pathlib import Path
            p = Path(models_dir) / "pca.joblib"
            if p.exists():
                data = joblib.load(p)
                self._pca_models = data
                logger.info(f"Loaded PCA models from {p}")
            b = Path(models_dir) / "baselines.joblib"
            if b.exists():
                baseline = joblib.load(b)
                self._baseline_means = baseline.get("means", {})
                self._baseline_stds = baseline.get("stds", {})
                logger.info(f"Loaded baselines from {b}")
        except Exception as e:
            logger.warning(f"Failed to load PCA/baselines: {e}")

    def add_reading(self, reading: SensorReading) -> None:
        self._windows[reading.machine_id].append(reading)

    def extract(self, machine_id: str) -> Tuple[Dict[str, float], List[Dict[str, object]]]:
        """Extract features for given machine_id. Returns (feature_dict, top_moving_sensors)."""
        window = self._windows.get(machine_id)
        if not window or len(window) == 0:
            return {}, []

        # Collect sensor names from latest reading (all windows should have same keys but handle union)
        all_sensors = set()
        for r in window:
            all_sensors.update(r.sensors.keys())

        # Build matrix: readings x sensors, ordered by time
        sensor_list = sorted(all_sensors)
        mat = np.full((len(window), len(sensor_list)), np.nan, dtype=np.float64)
        for i, r in enumerate(window):
            for j, sname in enumerate(sensor_list):
                if sname in r.sensors:
                    try:
                        mat[i, j] = float(r.sensors[sname])
                    except Exception:
                        mat[i, j] = np.nan

        # nan handling: fill with 0
        mat = np.nan_to_num(mat, nan=0.0)

        feature_dict: Dict[str, float] = {}

        # For each sensor, compute rolling stats on window
        means = np.mean(mat, axis=0)
        stds = np.std(mat, axis=0)
        mins = np.min(mat, axis=0)
        maxs = np.max(mat, axis=0)
        # slope: linear trend over window indices
        x = np.arange(len(window))
        slopes = []
        for j in range(len(sensor_list)):
            y = mat[:, j]
            # least squares slope
            if len(x) > 1 and np.std(y) > 1e-9:
                # polyfit
                try:
                    slope = np.polyfit(x, y, 1)[0]
                except Exception:
                    slope = 0.0
            else:
                slope = 0.0
            slopes.append(slope)
        slopes = np.array(slopes)

        # rate of change: last - first
        roc = mat[-1] - mat[0] if len(window) > 1 else np.zeros(len(sensor_list))

        # z-score vs baseline (if available)
        baseline_means = self._baseline_means.get(machine_id, {})
        baseline_stds = self._baseline_stds.get(machine_id, {})

        top_moving: List[Dict[str, object]] = []

        for j, sname in enumerate(sensor_list):
            # prefix with sensor name
            feature_dict[f"{sname}_mean"] = float(means[j])
            feature_dict[f"{sname}_std"] = float(stds[j])
            feature_dict[f"{sname}_min"] = float(mins[j])
            feature_dict[f"{sname}_max"] = float(maxs[j])
            feature_dict[f"{sname}_slope"] = float(slopes[j])
            feature_dict[f"{sname}_roc"] = float(roc[j])
            # z-score vs baseline
            b_mean = baseline_means.get(sname)
            b_std = baseline_stds.get(sname)
            if b_mean is not None and b_std is not None and b_std > 1e-8:
                z = (means[j] - b_mean) / b_std
                feature_dict[f"{sname}_zscore"] = float(z)
                # deviation metric
                dev = abs(z)
                top_moving.append({"name": sname, "deviation": float(dev), "direction": "up" if z > 0 else "down", "slope": float(slopes[j]), "mean": float(means[j])})
            else:
                # use std of window as proxy
                if stds[j] > 1e-8:
                    z = (mat[-1, j] - means[j]) / (stds[j] + 1e-8)
                else:
                    z = 0.0
                feature_dict[f"{sname}_zscore"] = float(z)
                top_moving.append({"name": sname, "deviation": float(abs(z)), "direction": "up" if z > 0 else "down", "slope": float(slopes[j]), "mean": float(means[j])})

        # spike flag: if latest deviates > 3 std from window mean
        for j, sname in enumerate(sensor_list):
            if stds[j] > 1e-8:
                spike = abs(mat[-1, j] - means[j]) > 3 * stds[j]
                feature_dict[f"{sname}_spike"] = 1.0 if spike else 0.0

        # Sort top moving by deviation desc, take top 10
        top_moving_sorted = sorted(top_moving, key=lambda x: x["deviation"], reverse=True)[:10]

        # Dimensionality reduction for secom (if PCA available)
        machine_type = self._detect_machine_type(machine_id, window[-1])
        if machine_type == "secom" and machine_type in self._pca_models:
            pca = self._pca_models[machine_type]
            try:
                # create feature vector of means only for secom sensors (590)
                vec = means.reshape(1, -1)
                # pca expects fixed dimension – handle mismatch
                if hasattr(pca, "n_features_in_"):
                    if vec.shape[1] < pca.n_features_in_:
                        # pad
                        pad = np.zeros((1, pca.n_features_in_ - vec.shape[1]))
                        vec = np.concatenate([vec, pad], axis=1)
                    elif vec.shape[1] > pca.n_features_in_:
                        vec = vec[:, : pca.n_features_in_]
                reduced = pca.transform(vec)
                for idx, val in enumerate(reduced[0]):
                    feature_dict[f"pca_{idx}"] = float(val)
            except Exception as e:
                logger.debug(f"PCA transform failed for {machine_id}: {e}")

        return feature_dict, top_moving_sorted

    def _detect_machine_type(self, machine_id: str, reading: SensorReading) -> str:
        return reading.machine_type

    def window_full(self, machine_id: str) -> bool:
        w = self._windows.get(machine_id)
        return w is not None and len(w) >= self.window_size

    def reset(self, machine_id: str | None = None) -> None:
        if machine_id:
            self._windows.pop(machine_id, None)
        else:
            self._windows.clear()

    def get_window(self, machine_id: str) -> List[SensorReading]:
        return list(self._windows.get(machine_id, []))
