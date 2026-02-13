from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate


def validate_file(schema_path: str, data_path: str) -> None:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    data = json.loads(Path(data_path).read_text(encoding="utf-8"))
    validate(instance=data, schema=schema)


def validate_data(schema_path: str, data: dict) -> None:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    validate(instance=data, schema=schema)


def validate_instance(schema_path: str, instance: object) -> None:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    validate(instance=instance, schema=schema)
