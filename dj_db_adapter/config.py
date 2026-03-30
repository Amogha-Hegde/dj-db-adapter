from __future__ import annotations

import os
from json import loads as json_loads
from pathlib import Path
from typing import Any

from dj_db_adapter.backends import normalize_database_config
from dj_db_adapter.backends import parse_database_url
from dj_db_adapter.backends import register_backend

DatabaseConfig = dict[str, Any]

ENV_FIELD_MAP: tuple[tuple[str, str], ...] = (
    ("DJANGO_DB_NAME", "NAME"),
    ("DJANGO_DB_USER", "USER"),
    ("DJANGO_DB_PASSWORD", "PASSWORD"),
    ("DJANGO_DB_HOST", "HOST"),
    ("DJANGO_DB_PORT", "PORT"),
    ("DJANGO_DB_ACCOUNT", "ACCOUNT"),
    ("DJANGO_DB_SCHEMA", "SCHEMA"),
    ("DJANGO_DB_WAREHOUSE", "WAREHOUSE"),
    ("DJANGO_DB_ROLE", "ROLE"),
    ("DJANGO_DB_PROJECT", "PROJECT"),
    ("DJANGO_DB_INSTANCE", "INSTANCE"),
    ("DJANGO_DB_TIME_ZONE", "TIME_ZONE"),
    ("DJANGO_DB_LOAD_BALANCE", "LOAD_BALANCE"),
    ("DJANGO_DB_TOPOLOGY_KEYS", "TOPOLOGY_KEYS"),
)


def read_setting(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is not None:
        return value

    file_path = os.getenv(f"{name}_FILE")
    if not file_path:
        return default

    return Path(file_path).read_text(encoding="utf-8").strip()


def _read_bool(name: str) -> bool | None:
    value = read_setting(name)
    if value is None:
        return None
    return value.lower() in {"1", "true", "yes", "on"}


def _read_json_object(name: str) -> dict[str, Any]:
    raw_value = read_setting(name)
    if not raw_value:
        return {}

    loaded_value = json_loads(raw_value)
    if not isinstance(loaded_value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return {str(key): value for key, value in loaded_value.items()}


def parse(
    url: str,
    *,
    conn_max_age: int | None = None,
    conn_health_checks: bool | None = None,
    options: dict[str, Any] | None = None,
) -> DatabaseConfig:
    config = parse_database_url(url)
    if conn_max_age is not None:
        config["CONN_MAX_AGE"] = conn_max_age
    if conn_health_checks is not None:
        config["CONN_HEALTH_CHECKS"] = conn_health_checks

    merged_options = dict(config.get("OPTIONS", {}))
    if options:
        merged_options.update(options)
    if merged_options:
        config["OPTIONS"] = merged_options
    else:
        config.pop("OPTIONS", None)

    return normalize_database_config(config)


def config(
    default: str | None = None,
    *,
    env: str = "DATABASE_URL",
    base_dir: str | Path | None = None,
) -> DatabaseConfig:
    if base_dir is None:
        default_sqlite_name: str | Path = Path("db.sqlite3")
    else:
        default_sqlite_name = Path(base_dir) / "db.sqlite3"

    db_config: DatabaseConfig = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": default_sqlite_name,
    }

    database_url = read_setting(env, default)
    if database_url:
        db_config = parse_database_url(database_url)

    engine = read_setting("DJANGO_DB_ENGINE")
    if engine:
        db_config["ENGINE"] = engine

    for env_name, setting_name in ENV_FIELD_MAP:
        value = read_setting(env_name)
        if value is not None:
            db_config[setting_name] = value

    conn_max_age = read_setting("DJANGO_DB_CONN_MAX_AGE")
    if conn_max_age is not None:
        db_config["CONN_MAX_AGE"] = int(conn_max_age)

    conn_health_checks = _read_bool("DJANGO_DB_CONN_HEALTH_CHECKS")
    if conn_health_checks is not None:
        db_config["CONN_HEALTH_CHECKS"] = conn_health_checks

    disable_server_side_cursors = _read_bool("DJANGO_DB_DISABLE_SERVER_SIDE_CURSORS")
    if disable_server_side_cursors is not None:
        db_config["DISABLE_SERVER_SIDE_CURSORS"] = disable_server_side_cursors

    atomic_requests = _read_bool("DJANGO_DB_ATOMIC_REQUESTS")
    if atomic_requests is not None:
        db_config["ATOMIC_REQUESTS"] = atomic_requests

    autocommit = _read_bool("DJANGO_DB_AUTOCOMMIT")
    if autocommit is not None:
        db_config["AUTOCOMMIT"] = autocommit

    options = dict(db_config.get("OPTIONS", {}))
    options.update(_read_json_object("DJANGO_DB_OPTIONS"))
    if options:
        db_config["OPTIONS"] = options
    else:
        db_config.pop("OPTIONS", None)

    test_config = dict(db_config.get("TEST", {}))
    test_config.update(_read_json_object("DJANGO_DB_TEST"))
    if test_config:
        db_config["TEST"] = test_config
    else:
        db_config.pop("TEST", None)

    db_config.update(_read_json_object("DJANGO_DB_SETTINGS"))
    return normalize_database_config(db_config)
