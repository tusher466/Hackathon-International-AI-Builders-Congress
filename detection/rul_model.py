"""RUL model for turbofan."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


class RULModel:
    """Regressor for remaining useful life."""

    def __init__(self, model_type: str = "rf"):
        self.model_type = model_type
        self.model: Optional[RandomForestRegressor | GradientBoostingRegressor] = None
        self.feature_names: List[str] = []
        self.mae: Optional[float] = None

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Dict[str, float]:
        """Fit regressor, returns metrics."""
        self.feature_names = feature_names
        logger.info(f"Training RUL model X={X.shape} y={y.shape}")
        # Split held-out engine split: simple train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        if self.model_type == "gb":
            self.model = GradientBoostingRegressor(random_state=42)
        else:
            self.model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)

        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        self.mae = float(mean_absolute_error(y_test, y_pred))
        logger.info(f"RUL model trained MAE={self.mae:.2f}")
        return {"mae": self.mae, "train_size": len(X_train), "test_size": len(X_test)}

    def predict_rul(self, features: Dict[str, float]) -> Tuple[float, float]:
        """Predict RUL and confidence proxy (spread across trees)."""
        if self.model is None:
            return 100.0, 0.5  # default

        vec = [features.get(fn, 0.0) for fn in self.feature_names]
        X = np.array(vec).reshape(1, -1)
        try:
            pred = float(self.model.predict(X)[0])
            # confidence proxy: spread across ensemble trees
            if hasattr(self.model, "estimators_"):
                # for RF, get individual tree predictions
                tree_preds = []
                for est in self.model.estimators_[:20]:  # sample 20 trees for speed
                    try:
                        tree_preds.append(float(est.predict(X)[0]))
                    except Exception:
                        pass
                if tree_preds:
                    std = float(np.std(tree_preds))
                    # confidence inverse to std: high spread -> low confidence
                    # map std to 0-1 confidence: assume std up to 50 cycles is low confidence
                    confidence = float(np.clip(1.0 - std / 50.0, 0.1, 0.99))
                else:
                    confidence = 0.7
            else:
                confidence = 0.7

            # Clip RUL to non-negative
            pred = max(0.0, pred)
            return pred, confidence
        except Exception as e:
            logger.warning(f"RUL predict failed: {e}")
            return 100.0, 0.3

    def save(self, models_dir: str = "./models") -> None:
        import joblib
        Path(models_dir).mkdir(parents=True, exist_ok=True)
        if self.model is not None:
            joblib.dump(self.model, Path(models_dir) / "rul_model.joblib")
            joblib.dump({"feature_names": self.feature_names, "mae": self.mae}, Path(models_dir) / "rul_meta.joblib")
            logger.info("Saved RUL model")

    def load(self, models_dir: str = "./models") -> bool:
        import joblib
        from pathlib import Path
        p = Path(models_dir)
        try:
            model_path = p / "rul_model.joblib"
            meta_path = p / "rul_meta.joblib"
            if model_path.exists():
                self.model = joblib.load(model_path)
                if meta_path.exists():
                    meta = joblib.load(meta_path)
                    self.feature_names = meta.get("feature_names", [])
                    self.mae = meta.get("mae")
                logger.info("Loaded RUL model")
                return True
        except Exception as e:
            logger.warning(f"Failed to load RUL model: {e}")
        return False
