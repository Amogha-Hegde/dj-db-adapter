from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dj_db_adapter.backends import normalize_database_config
from dj_db_adapter.backends import parse_database_url
from dj_db_adapter.backends import resolve_backend
from dj_db_adapter.backends.base import COMMON_ENV_MAP
from dj_db_adapter.backends.base import bool_from_string
from dj_db_adapter.file_formats import load_config_file

DatabaseConfig = dict[str, Any]
DatabasesConfig = dict[str, DatabaseConfig]


def read_setting(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is not None:
        return value
    file_path = os.getenv(f"{name}_FILE")
    if not file_path:
        return default
    return Path(file_path).read_text(encoding="utf-8").strip()


def _alias_token(alias: str) -> str:
    return alias.upper().replace("-", "_")


def _alias_env_names(alias: str, suffix: str) -> list[str]:
    token = _alias_token(alias)
    names = [f"DJANGO_DATABASE_{token}_{suffix}"]
    if alias == "default":
        names.extend([f"DJANGO_DATABASE_{suffix}", suffix if suffix == "URL" else ""])
    return [name for name in names if name]


def _read_alias_setting(alias: str, suffix: str, default: str | None = None) -> str | None:
    for name in _alias_env_names(alias, suffix):
        value = read_setting(name)
        if value is not None:
            return value
    return default


def _read_alias_path(alias: str, suffix: str) -> str | None:
    for name in _alias_env_names(alias, suffix):
        direct = os.getenv(name)
        if direct is not None:
            return direct
        from_file = os.getenv(f"{name}_FILE")
        if from_file is not None:
            return from_file
    return None


def _read_json(alias: str, suffix: str) -> dict[str, Any]:
    raw_value = _read_alias_setting(alias, suffix)
    if not raw_value:
        return {}
    loaded = json.loads(raw_value)
    if not isinstance(loaded, dict):
        raise ValueError(f"{suffix} must be a JSON object")
    return {str(key): value for key, value in loaded.items()}


def _coerce_common_settings(config: DatabaseConfig) -> DatabaseConfig:
    normalized = dict(config)
    if "CONN_MAX_AGE" in normalized:
        normalized["CONN_MAX_AGE"] = int(normalized["CONN_MAX_AGE"])
    for key in ("ATOMIC_REQUESTS", "AUTOCOMMIT", "CONN_HEALTH_CHECKS", "DISABLE_SERVER_SIDE_CURSORS"):
        if key in normalized and isinstance(normalized[key], str):
            normalized[key] = bool_from_string(normalized[key])
    return normalized


def _default_sqlite_config(base_dir: str | Path | None) -> DatabaseConfig:
    base_path = Path(base_dir) if base_dir is not None else Path.cwd()
    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": base_path / "db.sqlite3",
    }


def _resolve_backend_name(source: DatabaseConfig, alias: str, default_engine: str | None = None) -> str:
    engine = str(source.get("ENGINE") or default_engine or "")
    if engine:
        backend = resolve_backend(engine)
        return backend.engine if backend is not None else engine
    url = source.get("URL")
    if isinstance(url, str) and url:
        return str(parse_database_url(url)["ENGINE"])
    if alias == "default":
        return "django.db.backends.sqlite3"
    raise ValueError(f"Alias '{alias}' requires ENGINE or URL")


def _validate_settings(alias: str, engine: str, config: DatabaseConfig) -> None:
    backend = resolve_backend(engine)
    if backend is None:
        return
    invalid = sorted(set(config) - backend.settings)
    if invalid:
        raise ValueError(
            f"Alias '{alias}' for engine '{engine}' received unsupported settings: {', '.join(invalid)}"
        )


def _config_from_file(alias: str) -> DatabaseConfig:
    file_path = _read_alias_path(alias, "CONFIG")
    if not file_path:
        return {}
    loaded = load_config_file(file_path)
    if "url" in loaded and "URL" not in loaded:
        loaded["URL"] = loaded.pop("url")
    if "engine" in loaded and "ENGINE" not in loaded:
        loaded["ENGINE"] = loaded.pop("engine")
    return {str(key).upper(): value for key, value in loaded.items()}


def _config_from_env(alias: str, engine: str | None) -> DatabaseConfig:
    env_config: DatabaseConfig = {}
    url = _read_alias_setting(alias, "URL")
    if url:
        env_config["URL"] = url

    engine_value = _read_alias_setting(alias, "ENGINE", engine)
    if engine_value:
        backend = resolve_backend(engine_value)
        env_config["ENGINE"] = backend.engine if backend is not None else engine_value

    effective_engine = str(env_config.get("ENGINE") or engine or "")
    if not effective_engine and alias == "default":
        effective_engine = "django.db.backends.sqlite3"
    backend = resolve_backend(effective_engine) if effective_engine else None

    for suffix, setting_name in COMMON_ENV_MAP:
        value = _read_alias_setting(alias, suffix)
        if value is not None:
            env_config[setting_name] = value

    if backend is not None:
        for suffix, setting_name in backend.env_map:
            value = _read_alias_setting(alias, suffix)
            if value is not None:
                env_config[setting_name] = value

    options = _read_json(alias, "OPTIONS")
    if options:
        env_config["OPTIONS"] = options

    test_config = _read_json(alias, "TEST")
    if test_config:
        env_config["TEST"] = test_config

    settings = _read_json(alias, "SETTINGS")
    env_config.update(settings)
    return env_config


def parse(url: str) -> DatabaseConfig:
    return normalize_database_config(parse_database_url(url))


def config(
    alias: str = "default",
    *,
    base_dir: str | Path | None = None,
) -> DatabaseConfig:
    file_config = _config_from_file(alias)
    file_engine = _resolve_backend_name(file_config, alias) if file_config else None
    env_config = _config_from_env(alias, file_engine)

    merged: DatabaseConfig = {}
    if alias == "default" and not file_config and "URL" not in env_config and "ENGINE" not in env_config:
        merged.update(_default_sqlite_config(base_dir))

    if file_config:
        merged.update(file_config)
    if env_config:
        merged.update(env_config)

    if "URL" in merged:
        parsed = parse_database_url(str(merged.pop("URL")))
        parsed.update(merged)
        merged = parsed

    engine = _resolve_backend_name(merged, alias, merged.get("ENGINE"))
    merged["ENGINE"] = engine
    _validate_settings(alias, engine, merged)
    merged = _coerce_common_settings(merged)
    return normalize_database_config(merged)


def databases(
    aliases: list[str] | tuple[str, ...] | None = None,
    *,
    base_dir: str | Path | None = None,
) -> DatabasesConfig:
    if aliases is None:
        raw_aliases = read_setting("DJANGO_DATABASE_ALIASES", "default") or "default"
        aliases = tuple(alias.strip() for alias in raw_aliases.split(",") if alias.strip())
    return {alias: config(alias, base_dir=base_dir) for alias in aliases}
