from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dj_db_adapter.backends import normalize_database_config
from dj_db_adapter.backends import parse_database_url
from dj_db_adapter.backends import resolve_backend
from dj_db_adapter.backends.base import COMMON_ENV_MAP
from dj_db_adapter.backends.base import BackendDefinition
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


def _env_name(alias: str, suffix: str) -> str:
    return f"DJ_DB_{_alias_token(alias)}_{suffix}"


def _read_alias_setting(alias: str, suffix: str, default: str | None = None) -> str | None:
    return read_setting(_env_name(alias, suffix), default)


def _read_alias_path(alias: str, suffix: str) -> str | None:
    name = _env_name(alias, suffix)
    direct = os.getenv(name)
    if direct is not None:
        return direct
    from_file = os.getenv(f"{name}_FILE")
    if from_file is not None:
        return from_file
    return None


def _coerce_common_settings(config: DatabaseConfig) -> DatabaseConfig:
    normalized = dict(config)
    if "CONN_MAX_AGE" in normalized:
        normalized["CONN_MAX_AGE"] = int(normalized["CONN_MAX_AGE"])
    for key in ("ATOMIC_REQUESTS", "AUTOCOMMIT", "CONN_HEALTH_CHECKS", "DISABLE_SERVER_SIDE_CURSORS"):
        if key in normalized and isinstance(normalized[key], str):
            normalized[key] = bool_from_string(normalized[key])
    return normalized


def _normalize_loaded_file_config(loaded: dict[str, Any]) -> DatabaseConfig:
    normalized = {str(key).upper(): value for key, value in loaded.items()}
    if "URL" not in normalized and "url" in loaded:
        normalized["URL"] = loaded["url"]
    if "ENGINE" not in normalized and "engine" in loaded:
        normalized["ENGINE"] = loaded["engine"]
    if "BACKEND" not in normalized and "backend" in loaded:
        normalized["BACKEND"] = loaded["backend"]
    return normalized


def _config_from_file(alias: str) -> DatabaseConfig:
    file_path = _read_alias_path(alias, "CONFIG_FILE")
    if not file_path:
        return {}
    return _normalize_loaded_file_config(load_config_file(file_path))


def _backend_from_selector(value: str | None) -> BackendDefinition | None:
    if not value:
        return None
    return resolve_backend(value)


def _resolve_engine(
    alias: str,
    *,
    backend_name: str | None,
    engine_override: str | None,
    source: DatabaseConfig,
) -> tuple[str, BackendDefinition | None]:
    if engine_override:
        backend = resolve_backend(engine_override)
        return (backend.engine if backend is not None else engine_override, backend)

    backend = _backend_from_selector(backend_name)
    if backend is not None:
        return backend.engine, backend

    source_engine = source.get("ENGINE")
    if isinstance(source_engine, str) and source_engine:
        backend = resolve_backend(source_engine)
        return (backend.engine if backend is not None else source_engine, backend)

    source_backend = source.get("BACKEND")
    if isinstance(source_backend, str) and source_backend:
        backend = _backend_from_selector(source_backend)
        if backend is not None:
            return backend.engine, backend

    url = source.get("URL")
    if isinstance(url, str) and url:
        parsed = parse_database_url(url)
        engine = str(parsed["ENGINE"])
        return engine, resolve_backend(engine)

    raise ValueError(f"Alias '{alias}' requires BACKEND, ENGINE, URL, or CONFIG_FILE")


def _config_from_backend_env(alias: str, backend: BackendDefinition) -> DatabaseConfig:
    env_config: DatabaseConfig = {}
    backend_token = backend.env_prefix

    for suffix, setting_name in backend.env_map:
        value = read_setting(_env_name(alias, f"{backend_token}_{suffix}"))
        if value is not None:
            env_config[setting_name] = value

    for suffix, setting_name in COMMON_ENV_MAP:
        value = read_setting(_env_name(alias, f"{backend_token}_{suffix}"))
        if value is not None:
            env_config[setting_name] = value

    options_prefix = f"{_env_name(alias, backend_token)}__OPTIONS__"
    options: dict[str, Any] = {}
    for key, value in os.environ.items():
        if not key.startswith(options_prefix):
            continue
        option_name = key.removeprefix(options_prefix)
        normalized_name = option_name.lower()
        if backend.allowed_options and normalized_name not in {item.lower() for item in backend.allowed_options}:
            raise ValueError(
                f"Alias '{alias}' for backend '{backend.env_prefix}' received unsupported option '{option_name}'"
            )
        allowed_name = next(
            (item for item in backend.allowed_options if item.lower() == normalized_name),
            option_name.lower(),
        )
        options[allowed_name] = value
    if options:
        env_config["OPTIONS"] = options

    return env_config


def _validate_settings(alias: str, engine: str, config: DatabaseConfig) -> None:
    backend = resolve_backend(engine)
    if backend is None:
        return
    invalid = sorted(set(config) - backend.settings)
    if invalid:
        raise ValueError(
            f"Alias '{alias}' for engine '{engine}' received unsupported settings: {', '.join(invalid)}"
        )

    options = config.get("OPTIONS")
    if backend.allowed_options and isinstance(options, dict):
        invalid_options = sorted(
            key for key in options if key.lower() not in {item.lower() for item in backend.allowed_options}
        )
        if invalid_options:
            raise ValueError(
                f"Alias '{alias}' for backend '{backend.env_prefix}' received unsupported option(s): "
                f"{', '.join(invalid_options)}"
            )


def parse(url: str) -> DatabaseConfig:
    return normalize_database_config(parse_database_url(url))


def config(
    alias: str = "default",
) -> DatabaseConfig:
    file_config = _config_from_file(alias)
    url = _read_alias_setting(alias, "URL")
    backend_name = _read_alias_setting(alias, "BACKEND")
    engine_override = _read_alias_setting(alias, "ENGINE")

    merged: DatabaseConfig = {}
    if file_config:
        merged.update(file_config)
    if url:
        merged["URL"] = url
    if backend_name:
        merged["BACKEND"] = backend_name
    if engine_override:
        merged["ENGINE"] = engine_override

    engine, backend = _resolve_engine(
        alias,
        backend_name=backend_name,
        engine_override=engine_override,
        source=merged,
    )

    if "URL" in merged:
        parsed = parse_database_url(str(merged.pop("URL")))
        parsed.update(merged)
        merged = parsed

    if backend is None:
        backend = resolve_backend(engine)

    if backend is not None:
        merged.update(_config_from_backend_env(alias, backend))

    merged["ENGINE"] = engine
    merged.pop("BACKEND", None)
    _validate_settings(alias, engine, merged)
    merged = _coerce_common_settings(merged)
    return normalize_database_config(merged)


def databases(
    aliases: list[str] | tuple[str, ...] | None = None,
) -> DatabasesConfig:
    if aliases is None:
        raw_aliases = read_setting("DJ_DB_ALIASES", "") or ""
        aliases = tuple(alias.strip() for alias in raw_aliases.split(",") if alias.strip())
    return {alias: config(alias) for alias in aliases}
