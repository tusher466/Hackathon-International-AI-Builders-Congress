"""Notifier with pluggable channels."""
from __future__ import annotations

import logging
import json
from typing import Dict, Any, List
import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)


class Notifier:
    """Pluggable channels: console log always on, webhook optional."""

    def __init__(self):
        self.settings = get_settings()

    def notify(self, event_type: str, payload: Dict[str, Any]) -> List[str]:
        """Send notifications via all channels. Never fails pipeline."""
        results = []
        # Console log always
        try:
            logger.info(f"Notifier {event_type}: {json.dumps(payload, default=str)[:500]}")
            results.append(f"console:{event_type}")
        except Exception as e:
            logger.warning(f"Console notify failed: {e}")

        # Webhook if configured
        if self.settings.WEBHOOK_URL:
            try:
                # Slack-compatible payload
                slack_payload = {
                    "text": f"Factory Brain event: {event_type}",
                    "attachments": [
                        {
                            "title": event_type,
                            "text": json.dumps(payload, default=str)[:2000],
                        }
                    ],
                }
                # Use sync httpx for simplicity
                with httpx.Client(timeout=5.0) as client:
                    resp = client.post(self.settings.WEBHOOK_URL, json=slack_payload)
                    results.append(f"webhook:{resp.status_code}")
            except Exception as e:
                # Never fail pipeline
                logger.warning(f"Webhook notify failed: {e}")
                results.append(f"webhook_failed:{e}")

        return results


# Global singleton
_global_notifier: Notifier | None = None


def get_notifier() -> Notifier:
    global _global_notifier
    if _global_notifier is None:
        _global_notifier = Notifier()
    return _global_notifier


def notify_event(event_type: str, payload: Dict[str, Any]) -> List[str]:
    return get_notifier().notify(event_type, payload)
