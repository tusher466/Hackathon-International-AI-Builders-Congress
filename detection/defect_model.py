"""Defect classifier for Bosch."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, matthews_corrcoef
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


class DefectModel:
    """Classifier for Bosch defects."""

    def __init__(self, model_type: str = "rf"):
        self.model_type = model_type
        self.model = None
        self.feature_names: List[str] = []
        self.metrics: Dict[str, float] = {}

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Dict[str, float]:
        self.feature_names = feature_names
        logger.info(f"Training defect model X={X.shape} y sum={np.sum(y)}")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y))>1 else None)

        if self.model_type == "gb":
            self.model = GradientBoostingClassifier(random_state=42)
        else:
            self.model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced", n_jobs=-1)

        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        try:
            y_proba = self.model.predict_proba(X_test)[:, 1]
        except Exception:
            y_proba = y_pred

        precision = float(precision_score(y_test, y_pred, zero_division=0))
        recall = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        try:
            mcc = float(matthews_corrcoef(y_test, y_pred))
        except Exception:
            mcc = 0.0

        self.metrics = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "mcc": mcc,
            "train_size": len(X_train),
            "test_size": len(X_test),
        }
        logger.info(f"Defect model metrics: {self.metrics}")
        return self.metrics

    def predict_defect(self, features: Dict[str, float]) -> Tuple[float, float]:
        """Return defect_probability and confidence."""
        if self.model is None:
            return 0.0, 0.5

        vec = [features.get(fn, 0.0) for fn in self.feature_names]
        X = np.array(vec).reshape(1, -1)
        try:
            if hasattr(self.model, "predict_proba"):
                proba = float(self.model.predict_proba(X)[0][1])
            else:
                proba = float(self.model.predict(X)[0])
            # confidence: distance from 0.5
            confidence = float(abs(proba - 0.5) * 2)  # 0 low, 1 high
            confidence = np.clip(confidence, 0.1, 0.99)
            return proba, confidence
        except Exception as e:
            logger.warning(f"Defect predict failed: {e}")
            return 0.0, 0.3

    def save(self, models_dir: str = "./models") -> None:
        import joblib
        Path(models_dir).mkdir(parents=True, exist_ok=True)
        if self.model is not None:
            joblib.dump(self.model, Path(models_dir) / "defect_model.joblib")
            joblib.dump({"feature_names": self.feature_names, "metrics": self.metrics}, Path(models_dir) / "defect_meta.joblib")
            logger.info("Saved defect model")

    def load(self, models_dir: str = "./models") -> bool:
        import joblib
        from pathlib import Path
        p = Path(models_dir)
        try:
            model_path = p / "defect_model.joblib"
            meta_path = p / "defect_meta.joblib"
            if model_path.exists():
                self.model = joblib.load(model_path)
                if meta_path.exists():
                    meta = joblib.load(meta_path)
                    self.feature_names = meta.get("feature_names", [])
                    self.metrics = meta.get("metrics", {})
                logger.info("Loaded defect model")
                return True
        except Exception as e:
            logger.warning(f"Failed to load defect model: {e}")
        return False
