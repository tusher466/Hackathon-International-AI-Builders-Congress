"""Anomaly detection per machine_type using Isolation Forest."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
from sklearn.ensemble import IsolationForest

from config.settings import get_settings

logger = logging.getLogger(__name__)


class AnomalyModel:
    """Isolation Forest per machine_type."""

    def __init__(self):
        self.models: Dict[str, IsolationForest] = {}
        self.baseline_means: Dict[str, Dict[str, float]] = {}
        self.baseline_stds: Dict[str, Dict[str, float]] = {}
        self.feature_names: Dict[str, List[str]] = {}

    def fit(self, machine_type: str, X: np.ndarray, feature_names: List[str]) -> None:
        """Fit Isolation Forest.

        Args:
            machine_type: type id
            X: shape (n_samples, n_features)
            feature_names: list of names aligned with X columns
        """
        logger.info(f"Training anomaly model for {machine_type} X.shape={X.shape}")
        model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
        model.fit(X)
        self.models[machine_type] = model
        self.feature_names[machine_type] = feature_names
        # baseline mean/std per feature for deviation calculation
        mean = np.mean(X, axis=0)
        std = np.std(X, axis=0)
        self.baseline_means[machine_type] = {name: float(mean[i]) for i, name in enumerate(feature_names)}
        self.baseline_stds[machine_type] = {name: float(std[i] if std[i] > 1e-8 else 1.0) for i, name in enumerate(feature_names)}

    def score(self, machine_type: str, features: Dict[str, float]) -> Tuple[float, List[Dict[str, object]]]:
        """Score features, returns anomaly_score in [0,1] and top contributing sensors."""
        model = self.models.get(machine_type)
        if model is None:
            # no model -> return 0
            return 0.0, []

        feature_names = self.feature_names.get(machine_type, [])
        # Build vector in model order
        vec = []
        for fname in feature_names:
            vec.append(features.get(fname, 0.0))
        X = np.array(vec).reshape(1, -1)

        # decision_function gives opposite of anomaly; lower = more anomalous
        # We convert to [0,1] where 1 = highly anomalous
        # IsolationForest decision_function: average anomaly score, shifted
        try:
            dec = model.decision_function(X)[0]  # higher is normal
            # map: decision ~ 0 for boundary, negative for anomaly
            # convert: score = 0.5 - dec (clipped) then scaled to [0,1]
            # Use score_samples for more stable: opposite of anomaly score
            raw_score = model.score_samples(X)[0]  # opposite of anomaly, lower = more anomalous
            # Normalize via min-max heuristics: we'll map raw_score to [0,1] anomaly
            # score_samples is typically negative, more negative = anomaly
            # Let's convert: anomaly_score = 1 - sigmoid(raw_score)
            # Simpler: use known contamination: transform decision
            # Standard scaling: decision_function mean? Use formula: 0.5 - decision_function clipped
            # We'll use: anomaly = 1 - (dec + 0.5) clipped
            # Actually decision_function: inlier ~ positive, outlier negative.
            # So anomaly_score = (-dec) scaled to 0-1
            anomaly = float(np.clip(-dec, 0, 1))  # 0 normal, 1 highly anomalous
            # Also incorporate raw_score for spread
            # Adjust: if raw_score very low (< -0.5) increase score
            if raw_score < -0.5:
                anomaly = min(1.0, anomaly + 0.2)
        except Exception as e:
            logger.warning(f"Anomaly scoring failed for {machine_type}: {e}")
            anomaly = 0.0

        # top contributing sensors: per-feature deviation from baseline mean in standardized units
        means = self.baseline_means.get(machine_type, {})
        stds = self.baseline_stds.get(machine_type, {})
        contributions = []
        for fname in feature_names:
            val = features.get(fname, 0.0)
            b_mean = means.get(fname, 0.0)
            b_std = stds.get(fname, 1.0)
            if b_std < 1e-8:
                b_std = 1.0
            deviation = (val - b_mean) / b_std
            contributions.append({"name": fname, "deviation": float(deviation), "direction": "up" if deviation > 0 else "down", "value": float(val)})

        # sort by abs deviation
        contributions_sorted = sorted(contributions, key=lambda x: abs(x["deviation"]), reverse=True)[:10]
        return anomaly, contributions_sorted

    def predict(self, machine_type: str, features: Dict[str, float], threshold: float = 0.5) -> bool:
        score, _ = self.score(machine_type, features)
        return score >= threshold

    def save(self, models_dir: str = "./models") -> None:
        import joblib
        from pathlib import Path
        Path(models_dir).mkdir(parents=True, exist_ok=True)
        for mtype, model in self.models.items():
            path = Path(models_dir) / f"anomaly_{mtype}.joblib"
            joblib.dump(model, path)
        # save metadata
        meta = {
            "baseline_means": self.baseline_means,
            "baseline_stds": self.baseline_stds,
            "feature_names": self.feature_names,
        }
        joblib.dump(meta, Path(models_dir) / "anomaly_meta.joblib")
        logger.info(f"Saved anomaly models to {models_dir}")

    def load(self, models_dir: str = "./models") -> bool:
        import joblib
        from pathlib import Path
        p = Path(models_dir)
        if not p.exists():
            return False
        try:
            meta_path = p / "anomaly_meta.joblib"
            if meta_path.exists():
                meta = joblib.load(meta_path)
                self.baseline_means = meta.get("baseline_means", {})
                self.baseline_stds = meta.get("baseline_stds", {})
                self.feature_names = meta.get("feature_names", {})
            for mtype_file in p.glob("anomaly_*.joblib"):
                if mtype_file.name == "anomaly_meta.joblib":
                    continue
                mtype = mtype_file.stem.replace("anomaly_", "")
                model = joblib.load(mtype_file)
                self.models[mtype] = model
            logger.info(f"Loaded {len(self.models)} anomaly models")
            return len(self.models) > 0
        except Exception as e:
            logger.warning(f"Failed to load anomaly models: {e}")
            return False
