from __future__ import annotations

import configparser
import json
from pathlib import Path
from typing import Any


def load_config_file(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    text = file_path.read_text(encoding="utf-8")

    if suffix == ".json":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError(f"{file_path} must contain a JSON object")
        return data

    if suffix in {".ini", ".cfg"}:
        parser = configparser.ConfigParser()
        parser.read_string(text)
        data: dict[str, Any] = {}
        source = parser["database"] if parser.has_section("database") else parser.defaults()
        for key, value in source.items():
            data[key.upper()] = value
        if parser.has_section("options"):
            data["OPTIONS"] = {key: value for key, value in parser["options"].items()}
        if parser.has_section("test"):
            data["TEST"] = {key.upper(): value for key, value in parser["test"].items()}
        return data

    raise ValueError(f"Unsupported config file format: {file_path.suffix}")
