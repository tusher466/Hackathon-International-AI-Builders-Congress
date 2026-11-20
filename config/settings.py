"""Central configuration via pydantic-settings."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All env vars for Factory Brain.

    Choices made for ambiguous spec:
    - Thresholds are configurable via env; defaults documented here and in .env.example
    - Health score weights sum to 1.0
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    API_KEY: Optional[str] = None
    CORS_ORIGINS: str = "*"

    # Streaming
    STREAM_BACKEND: Literal["mqtt", "memory"] = "memory"
    SIM_RATE_HZ: float = 2.0
    AUTO_START_STREAM: bool = True
    MQTT_HOST: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_TOPIC_PREFIX: str = "factory"
    MQTT_CLIENT_ID: str = "factory-brain"

    # LLM
    LLM_MODE: Literal["mock", "real"] = "mock"
    ANTHROPIC_API_KEY: Optional[str] = None
    LLM_MODEL: str = "claude-3-5-sonnet-20241022"
    LLM_MAX_RETRIES: int = 2

    # Storage
    DATABASE_URL: str = "sqlite:///./data/factory_brain.db"
    CHROMA_PERSIST_PATH: str = "./data/chroma"
    CHROMA_COLLECTION_NAME: str = "manuals"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RING_BUFFER_SIZE: int = 500
    MODELS_DIR: str = "./models"

    # Detection thresholds
    ANOMALY_THRESHOLD_LOW: float = 0.3
    ANOMALY_THRESHOLD_MEDIUM: float = 0.5
    ANOMALY_THRESHOLD_HIGH: float = 0.7
    ANOMALY_THRESHOLD_CRITICAL: float = 0.85

    RUL_CRITICAL: int = 20
    RUL_HIGH: int = 50
    RUL_MEDIUM: int = 100

    DEFECT_PROB_LOW: float = 0.3
    DEFECT_PROB_MEDIUM: float = 0.5
    DEFECT_PROB_HIGH: float = 0.7
    DEFECT_PROB_CRITICAL: float = 0.85

    ALERT_COOLDOWN_READINGS: int = 10
    FEATURE_WINDOW_SIZE: int = 30

    # Health score weights
    HEALTH_WEIGHT_ANOMALY: float = 0.4
    HEALTH_WEIGHT_RUL: float = 0.35
    HEALTH_WEIGHT_DEFECT: float = 0.15
    HEALTH_WEIGHT_ALERTS: float = 0.1
    HEALTH_OFFLINE_THRESHOLD_READINGS: int = 50

    # Agent
    MAX_CONCURRENT_AGENT_RUNS: int = 5
    MAX_AGENT_ITERATIONS: int = 8
    RETRIEVAL_K: int = 5
    RETRIEVAL_SCORE_THRESHOLD: float = 0.1

    # Actions
    WEBHOOK_URL: Optional[str] = None

    # Demo
    DEMO_FAULT_MACHINE: str = "TURBO-01"

    @property
    def is_mock_llm(self) -> bool:
        if self.LLM_MODE == "mock":
            return True
        if not self.ANTHROPIC_API_KEY:
            return True
        return False

    def ensure_dirs(self) -> None:
        Path(self.CHROMA_PERSIST_PATH).mkdir(parents=True, exist_ok=True)
        Path(self.MODELS_DIR).mkdir(parents=True, exist_ok=True)
        Path("./data/raw").mkdir(parents=True, exist_ok=True)
        Path("./data/processed").mkdir(parents=True, exist_ok=True)
        Path("./data/manuals").mkdir(parents=True, exist_ok=True)
        # handle sqlite dir
        db_path = self.DATABASE_URL.replace("sqlite:///", "")
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)


# Global singleton, but reloadable via function
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_dirs()
    return _settings


def reload_settings() -> Settings:
    global _settings
    _settings = Settings()
    _settings.ensure_dirs()
    return _settings
