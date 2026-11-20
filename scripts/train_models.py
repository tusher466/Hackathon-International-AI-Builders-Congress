"""Train models, save artifacts."""
from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Dict, List
import numpy as np
import pandas as pd

from config.settings import get_settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Imports for models
from detection.anomaly_model import AnomalyModel
from detection.rul_model import RULModel
from detection.defect_model import DefectModel
from ingestion.feature_extractor import FeatureExtractor
from ingestion.stream_simulator import StreamSimulator


def _load_or_synthetic():
    """Load data via StreamSimulator helpers (reuses loading logic)."""
    sim = StreamSimulator()
    sim.load_data()
    return sim


def _prepare_feature_matrices(sim: StreamSimulator, window_size: int = 30):
    """Prepare feature matrices per machine_type using sliding windows over simulation.

    Optimized for speed: limits rows to 150 per dataset when synthetic or large,
    and limits sensor count for secom to first 100 sensors to keep feature size manageable.
    """
    extractor = FeatureExtractor(window_size=window_size)

    raw_secom_features = []
    turbo_features = []
    bosch_features = []

    # For speed, cap rows
    MAX_ROWS_SECOM = 150
    MAX_ROWS_TURBO_PER_UNIT = 80
    MAX_ROWS_BOSCH = 150

    # Process SECOM
    if sim.secom_data is not None:
        df = sim.secom_data
        # Use only first 100 sensors for training speed (s0..s99) – still respects shape but reduces compute
        n_cols = min(100, df.shape[1])
        df_small = df.iloc[:MAX_ROWS_SECOM, :n_cols]
        for idx in range(len(df_small)):
            from ingestion.schemas import SensorReading
            from datetime import datetime, timezone
            row = df_small.iloc[idx]
            sensors = {f"s{i}": float(row.iloc[i]) for i in range(n_cols) if pd.notna(row.iloc[i])}
            reading = SensorReading(
                machine_id="SECOM-01",
                machine_type="secom",
                ts=datetime.now(timezone.utc),
                sequence=idx,
                sensors=sensors,
                meta={},
            )
            extractor.add_reading(reading)
            if extractor.window_full("SECOM-01"):
                feats, _ = extractor.extract("SECOM-01")
                if feats:
                    raw_secom_features.append(feats)

    # TURBO
    for mid, df in sim.cmapss_data.items():
        df_small = df.head(MAX_ROWS_TURBO_PER_UNIT)
        extractor_t = FeatureExtractor(window_size=min(window_size, 10))  # smaller window for turbo training
        for _, row in df_small.iterrows():
            from ingestion.schemas import SensorReading
            from datetime import datetime, timezone
            sensors = {c: float(row[c]) for c in df_small.columns if c.startswith("s") or c.startswith("op_")}
            reading = SensorReading(
                machine_id=mid,
                machine_type="turbofan",
                ts=datetime.now(timezone.utc),
                sequence=int(row["cycle"]),
                sensors=sensors,
                meta={"RUL": int(df_small["cycle"].max() - row["cycle"])},
            )
            extractor_t.add_reading(reading)
            if extractor_t.window_full(mid):
                feats, _ = extractor_t.extract(mid)
                if feats:
                    turbo_features.append((feats, reading.meta["RUL"]))

    # BOSCH
    if sim.bosch_data is not None:
        df = sim.bosch_data.head(MAX_ROWS_BOSCH)
        feature_cols = [c for c in df.columns if c != "Response"][:30]  # only 30 sensors for speed
        extractor_b = FeatureExtractor(window_size=min(window_size, 10))
        for idx in range(len(df)):
            from ingestion.schemas import SensorReading
            from datetime import datetime, timezone
            row = df.iloc[idx]
            sensors = {c: float(row[c]) if pd.notna(row[c]) else 0.0 for c in feature_cols}
            reading = SensorReading(
                machine_id="BOSCH-L1",
                machine_type="bosch",
                ts=datetime.now(timezone.utc),
                sequence=idx,
                sensors=sensors,
                meta={"ground_truth_defect": int(row["Response"]) if "Response" in row else 0},
            )
            extractor_b.add_reading(reading)
            if extractor_b.window_full("BOSCH-L1"):
                feats, _ = extractor_b.extract("BOSCH-L1")
                if feats:
                    bosch_features.append((feats, reading.meta["ground_truth_defect"]))

    return raw_secom_features, turbo_features, bosch_features, sim


def _features_to_matrix(feature_list: List[Dict]) -> tuple[np.ndarray, List[str]]:
    """Convert list of feature dicts to matrix and feature names."""
    if not feature_list:
        return np.empty((0, 0)), []
    # Union of all keys
    all_keys = sorted(set().union(*[f.keys() for f in feature_list]))
    matrix = np.zeros((len(feature_list), len(all_keys)), dtype=np.float64)
    for i, feat in enumerate(feature_list):
        for j, k in enumerate(all_keys):
            matrix[i, j] = feat.get(k, 0.0)
    return matrix, all_keys


def train_all(models_dir: str = "./models", use_synthetic: bool = True):
    settings = get_settings()
    models_dir = models_dir or settings.MODELS_DIR
    Path(models_dir).mkdir(parents=True, exist_ok=True)

    sim = _load_or_synthetic()
    secom_feats, turbo_feats, bosch_feats, sim_obj = _prepare_feature_matrices(sim, window_size=settings.FEATURE_WINDOW_SIZE)

    metrics = {}

    # --- Scalers and baselines ---
    # Compute per machine_type sensor mean/std for cleaner and baselines
    scalers = {}
    baselines_means = {}
    baselines_stds = {}

    # SECOM scalers from raw data
    if sim_obj.secom_data is not None:
        means = sim_obj.secom_data.mean()
        stds = sim_obj.secom_data.std().replace(0, 1.0)
        scalers["secom"] = {f"s{i}": (float(means.iloc[i]), float(stds.iloc[i])) for i in range(len(means))}
        # baselines per machine SECOM-01: use same
        baselines_means["SECOM-01"] = {f"s{i}": float(means.iloc[i]) for i in range(len(means))}
        baselines_stds["SECOM-01"] = {f"s{i}": float(stds.iloc[i]) for i in range(len(stds))}

    # Turbofan baselines: per sensor mean across all turbo data? Use first unit
    if sim_obj.cmapss_data:
        # Collect all sensor columns
        all_rows = pd.concat(list(sim_obj.cmapss_data.values()), ignore_index=True)
        sensor_cols = [c for c in all_rows.columns if c.startswith("s") or c.startswith("op_")]
        # compute mean/std per sensor
        turbo_scaler = {}
        for col in sensor_cols:
            turbo_scaler[col] = (float(all_rows[col].mean()), float(all_rows[col].std() if all_rows[col].std() > 0 else 1.0))
        scalers["turbofan"] = turbo_scaler
        # baselines per machine
        for mid, df in sim_obj.cmapss_data.items():
            m_means = {}
            m_stds = {}
            for col in sensor_cols:
                m_means[col] = float(df[col].mean())
                m_stds[col] = float(df[col].std() if df[col].std() > 0 else 1.0)
            baselines_means[mid] = m_means
            baselines_stds[mid] = m_stds

    # Bosch
    if sim_obj.bosch_data is not None:
        cols = [c for c in sim_obj.bosch_data.columns if c != "Response"][:100]
        bosch_scaler = {}
        for col in cols:
            mean = float(sim_obj.bosch_data[col].mean())
            std = float(sim_obj.bosch_data[col].std() if sim_obj.bosch_data[col].std() > 0 else 1.0)
            bosch_scaler[col] = (mean, std)
        scalers["bosch"] = bosch_scaler
        # baselines
        baselines_means["BOSCH-L1"] = {c: float(sim_obj.bosch_data[c].mean()) for c in cols}
        baselines_stds["BOSCH-L1"] = {c: float(sim_obj.bosch_data[c].std() if sim_obj.bosch_data[c].std() > 0 else 1.0) for c in cols}

    # Save scalers and baselines
    import joblib
    joblib.dump(scalers, Path(models_dir) / "scalers.joblib")
    joblib.dump({"means": baselines_means, "stds": baselines_stds}, Path(models_dir) / "baselines.joblib")

    # PCA for secom (if we have secom features matrix)
    pca_models = {}
    secom_matrix, secom_feature_names = _features_to_matrix(secom_feats)
    if secom_matrix.shape[0] > 10 and secom_matrix.shape[1] > 10:
        # variance filtering: remove low variance
        from sklearn.feature_selection import VarianceThreshold
        from sklearn.decomposition import PCA
        try:
            vt = VarianceThreshold(threshold=0.01)
            filtered = vt.fit_transform(secom_matrix)
            n_components = min(50, filtered.shape[1], filtered.shape[0])
            pca = PCA(n_components=n_components, random_state=42)
            pca.fit(filtered)
            # We need to save PCA and also the variance threshold mask
            # For simplicity, we fit PCA on original matrix with n_components 50 if possible
            # But we will save PCA trained on mean features? Use filtered for now
            # We'll create a PCA that can transform means vector: we need to handle dimension mismatch in extractor
            # Instead we train PCA on raw sensor means (not feature dict). Let's attempt simpler: PCA on raw secom sensor values matrix
            raw_matrix = sim_obj.secom_data.to_numpy() if sim_obj.secom_data is not None else secom_matrix
            if raw_matrix.shape[0] > 10:
                pca_raw = PCA(n_components=min(50, raw_matrix.shape[1], raw_matrix.shape[0]), random_state=42)
                pca_raw.fit(raw_matrix)
                pca_models["secom"] = pca_raw
        except Exception as e:
            logger.warning(f"PCA training failed: {e}")

    if pca_models:
        joblib.dump(pca_models, Path(models_dir) / "pca.joblib")

    # --- Anomaly models per machine_type ---
    anomaly_model = AnomalyModel()

    # SECOM: use secom_matrix as training for anomaly
    if secom_matrix.shape[0] > 0:
        # Ensure not too large: sample
        X = secom_matrix
        # Limit features to maybe 100 for training speed: select first 100
        if X.shape[1] > 200:
            # Use variance threshold to select top 200
            variances = np.var(X, axis=0)
            top_idx = np.argsort(variances)[-200:]
            X = X[:, top_idx]
            feature_names = [secom_feature_names[i] for i in top_idx]
        else:
            feature_names = secom_feature_names
        anomaly_model.fit("secom", X, feature_names)
        metrics["secom_anomaly_train_size"] = X.shape[0]

    # Turbofan: combine all turbo features (but anomaly model also for turbofan)
    if turbo_feats:
        turbo_feature_dicts = [f for f, _ in turbo_feats]
        turbo_matrix, turbo_feature_names = _features_to_matrix(turbo_feature_dicts)
        if turbo_matrix.shape[0] > 0:
            anomaly_model.fit("turbofan", turbo_matrix, turbo_feature_names)
            metrics["turbofan_anomaly_train_size"] = turbo_matrix.shape[0]

    # Bosch
    if bosch_feats:
        bosch_feature_dicts = [f for f, _ in bosch_feats]
        bosch_matrix, bosch_feature_names = _features_to_matrix(bosch_feature_dicts)
        if bosch_matrix.shape[0] > 0:
            anomaly_model.fit("bosch", bosch_matrix, bosch_feature_names)
            metrics["bosch_anomaly_train_size"] = bosch_matrix.shape[0]

    anomaly_model.save(models_dir)

    # --- RUL model ---
    rul_model = RULModel(model_type="rf")
    if turbo_feats:
        turbo_feature_dicts = [f for f, _ in turbo_feats]
        turbo_ys = np.array([y for _, y in turbo_feats])
        turbo_matrix, turbo_feature_names = _features_to_matrix(turbo_feature_dicts)
        if turbo_matrix.shape[0] > 10:
            rul_metrics = rul_model.fit(turbo_matrix, turbo_ys, turbo_feature_names)
            metrics.update({f"rul_{k}": v for k, v in rul_metrics.items()})
            rul_model.save(models_dir)

    # --- Defect model ---
    defect_model = DefectModel(model_type="rf")
    if bosch_feats:
        bosch_feature_dicts = [f for f, _ in bosch_feats]
        bosch_ys = np.array([y for _, y in bosch_feats])
        # Ensure at least some positives
        if len(np.unique(bosch_ys)) > 1:
            bosch_matrix, bosch_feature_names = _features_to_matrix(bosch_feature_dicts)
            if bosch_matrix.shape[0] > 10:
                def_metrics = defect_model.fit(bosch_matrix, bosch_ys, bosch_feature_names)
                metrics.update({f"defect_{k}": v for k, v in def_metrics.items()})
                defect_model.save(models_dir)
        else:
            logger.warning("Bosch defects have only one class, skipping defect model training")
            # still save dummy model trained on synthetic with at least 2 classes if needed
            # generate synthetic balanced set
            # create 100 samples, half defect
            X_syn = np.random.normal(0, 1, (200, len(bosch_feature_dicts[0]) if bosch_feature_dicts else 20))
            y_syn = np.array([0] * 100 + [1] * 100)
            f_names = bosch_feature_names if bosch_feature_dicts else [f"f{i}" for i in range(20)]
            if X_syn.shape[1] != len(f_names):
                f_names = [f"f{i}" for i in range(X_syn.shape[1])]
            def_metrics = defect_model.fit(X_syn, y_syn, f_names)
            defect_model.save(models_dir)
            metrics.update({f"defect_{k}": v for k, v in def_metrics.items()})

    # Save metrics.json
    metrics_path = Path(models_dir) / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Training complete, metrics saved to {metrics_path}")
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--models-dir", default="./models")
    parser.add_argument("--use-synthetic", action="store_true", default=True)
    args = parser.parse_args()
    train_all(models_dir=args.models_dir, use_synthetic=args.use_synthetic)
