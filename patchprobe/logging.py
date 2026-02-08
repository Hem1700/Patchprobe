import json
import logging
from datetime import datetime


def _json_formatter():
    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            payload = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "name": record.name,
                "message": record.getMessage(),
            }
            if hasattr(record, "job_id"):
                payload["job_id"] = getattr(record, "job_id")
            if hasattr(record, "stage"):
                payload["stage"] = getattr(record, "stage")
            return json.dumps(payload, sort_keys=True)

    return JsonFormatter()


def configure_logging(level: str = "INFO", log_path: str | None = None) -> None:
    logger = logging.getLogger()
    logger.setLevel(level)
    formatter = _json_formatter()

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if log_path:
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
