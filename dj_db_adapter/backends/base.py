from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import ParseResult, parse_qs, unquote

DatabaseConfig = dict[str, Any]
DatabaseParser = Callable[[ParseResult, str], DatabaseConfig]
DatabaseNormalizer = Callable[[DatabaseConfig], DatabaseConfig]


@dataclass(frozen=True)
class BackendDefinition:
    engine: str
    parser: DatabaseParser
    normalizer: DatabaseNormalizer | None = None
    aliases: tuple[str, ...] = field(default_factory=tuple)


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
    for key in ("USER", "PASSWORD", "HOST", "PORT"):
        normalized.pop(key, None)
    return normalized


def string_name_normalizer(config: DatabaseConfig) -> DatabaseConfig:
    normalized = dict(config)
    normalized["NAME"] = str(normalized.get("NAME", ""))
    return normalized
