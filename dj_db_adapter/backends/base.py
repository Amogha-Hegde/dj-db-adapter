from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import ParseResult, parse_qs, unquote

DatabaseConfig = dict[str, Any]
DatabaseParser = Callable[[ParseResult, str], DatabaseConfig]
DatabaseNormalizer = Callable[[DatabaseConfig], DatabaseConfig]

COMMON_SETTINGS = {
    "ATOMIC_REQUESTS",
    "AUTOCOMMIT",
    "CONN_HEALTH_CHECKS",
    "CONN_MAX_AGE",
    "DISABLE_SERVER_SIDE_CURSORS",
    "ENGINE",
    "OPTIONS",
    "TEST",
}

COMMON_ENV_MAP: tuple[tuple[str, str], ...] = (
    ("ATOMIC_REQUESTS", "ATOMIC_REQUESTS"),
    ("AUTOCOMMIT", "AUTOCOMMIT"),
    ("CONN_HEALTH_CHECKS", "CONN_HEALTH_CHECKS"),
    ("CONN_MAX_AGE", "CONN_MAX_AGE"),
    ("DISABLE_SERVER_SIDE_CURSORS", "DISABLE_SERVER_SIDE_CURSORS"),
)


@dataclass(frozen=True)
class BackendDefinition:
    engine: str
    parser: DatabaseParser
    aliases: tuple[str, ...]
    env_prefix: str
    env_map: tuple[tuple[str, str], ...]
    settings: frozenset[str]
    allowed_options: frozenset[str] = field(default_factory=frozenset)
    normalizer: DatabaseNormalizer | None = None
    default_name: str | Path | None = None


def query_options(parsed: ParseResult) -> dict[str, str]:
    return {key: values[-1] for key, values in parse_qs(parsed.query).items() if values}


def standard_parser(parsed: ParseResult, engine: str) -> DatabaseConfig:
    config: DatabaseConfig = {
        "ENGINE": engine,
        "NAME": parsed.path.lstrip("/"),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": parsed.port or "",
    }
    options = query_options(parsed)
    if options:
        config["OPTIONS"] = options
    return config


def sqlite_parser(parsed: ParseResult, engine: str) -> DatabaseConfig:
    if parsed.netloc == ":memory:" or parsed.path == ":memory:":
        name = ":memory:"
    elif parsed.netloc and parsed.path:
        name = f"//{parsed.netloc}{parsed.path}"
    elif parsed.netloc:
        name = parsed.netloc
    else:
        name = parsed.path or "/db.sqlite3"

    config: DatabaseConfig = {
        "ENGINE": engine,
        "NAME": unquote(name),
    }
    options = query_options(parsed)
    if options:
        config["OPTIONS"] = options
    return config


def sqlite_normalizer(config: DatabaseConfig) -> DatabaseConfig:
    normalized = dict(config)
    normalized["NAME"] = Path(str(normalized["NAME"]))
    normalized.pop("USER", None)
    normalized.pop("PASSWORD", None)
    normalized.pop("HOST", None)
    normalized.pop("PORT", None)
    return normalized


def string_name_normalizer(config: DatabaseConfig) -> DatabaseConfig:
    normalized = dict(config)
    if "NAME" in normalized:
        normalized["NAME"] = str(normalized["NAME"])
    return normalized


def bool_from_string(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "on"}


def base_settings(*settings: str) -> frozenset[str]:
    return frozenset(COMMON_SETTINGS | set(settings))
