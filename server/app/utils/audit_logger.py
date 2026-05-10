import json
import time
from pathlib import Path

from server.app.utils.privacy import redact_sensitive_text


class ClinicalAuditLogger:
    """
    Professional clinical logger for auditing AI interactions,
    tracking sentiment shifts and safety intercepts.
    """

    def __init__(self, log_path: str = "logs/clinical_audit.json"):
        self.log_path = Path(log_path)
        self.enabled = True
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.log_path.exists():
                with open(self.log_path, "w", encoding="utf-8") as f:
                    json.dump([], f)
        except OSError:
            # Audit logging should never block the assistant's response path.
            self.enabled = False

    def log_event(self, user_id: int | str, query: str, route: str, sentiment: str, safety_mode: str, processing_time: float):
        if not self.enabled:
            return

        event = {
            "timestamp": time.time(),
            "user_id": user_id,
            "query_preview": redact_sensitive_text(query)[:100],
            "route": route,
            "sentiment": sentiment,
            "safety_mode": safety_mode,
            "latency": processing_time,
        }

        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.append(event)
            # Keep only last 1000 events
            data = data[-1000:]
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
