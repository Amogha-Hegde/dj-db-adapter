from __future__ import annotations

from urllib.parse import ParseResult
from urllib.parse import unquote

from dj_db_adapter.backends.base import BackendDefinition
from dj_db_adapter.backends.base import DatabaseConfig
from dj_db_adapter.backends.base import query_options
from dj_db_adapter.backends.base import standard_parser
from dj_db_adapter.backends.base import string_name_normalizer


def mongodb_parser(parsed: ParseResult, engine: str) -> DatabaseConfig:
    return {
        "ENGINE": engine,
        "HOST": parsed.geturl(),
        "NAME": parsed.path.lstrip("/"),
    }


def spanner_parser(parsed: ParseResult, engine: str) -> DatabaseConfig:
    path_parts = [part for part in parsed.path.split("/") if part]
    config: DatabaseConfig = {
        "ENGINE": engine,
        "PROJECT": parsed.netloc,
        "INSTANCE": path_parts[0] if len(path_parts) > 0 else "",
        "NAME": path_parts[1] if len(path_parts) > 1 else "",
    }
    options = query_options(parsed)
    if options:
        config["OPTIONS"] = options
    return config


def snowflake_parser(parsed: ParseResult, engine: str) -> DatabaseConfig:
    path_parts = [part for part in parsed.path.split("/") if part]
    config: DatabaseConfig = {
        "ENGINE": engine,
        "NAME": path_parts[0] if len(path_parts) > 0 else "",
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "ACCOUNT": parsed.hostname or "",
    }
    if len(path_parts) > 1:
        config["SCHEMA"] = path_parts[1]

    options = query_options(parsed)
    warehouse = options.pop("warehouse", None)
    role = options.pop("role", None)
    if warehouse:
        config["WAREHOUSE"] = warehouse
    if role:
        config["ROLE"] = role
    if options:
        config["OPTIONS"] = options
    return config


def mongodb_normalizer(config: DatabaseConfig) -> DatabaseConfig:
    normalized = dict(config)
    normalized["NAME"] = str(normalized.get("NAME", ""))
    normalized.pop("PORT", None)
    return normalized


THIRD_PARTY_BACKENDS: tuple[BackendDefinition, ...] = (
    BackendDefinition(
        engine="django_cockroachdb",
        parser=standard_parser,
        normalizer=string_name_normalizer,
        aliases=("cockroach", "cockroachdb"),
    ),
    BackendDefinition(
        engine="django_firebird",
        parser=standard_parser,
        normalizer=string_name_normalizer,
        aliases=("firebird",),
    ),
    BackendDefinition(
        engine="django_spanner",
        parser=spanner_parser,
        normalizer=string_name_normalizer,
        aliases=("google-cloud-spanner", "spanner"),
    ),
    BackendDefinition(
        engine="mssql",
        parser=standard_parser,
        normalizer=string_name_normalizer,
        aliases=("microsoft-sql-server", "mssql"),
    ),
    BackendDefinition(
        engine="django_snowflake",
        parser=snowflake_parser,
        normalizer=string_name_normalizer,
        aliases=("snowflake",),
    ),
    BackendDefinition(
        engine="django_tidb",
        parser=standard_parser,
        normalizer=string_name_normalizer,
        aliases=("tidb",),
    ),
    BackendDefinition(
        engine="django.db.backends.postgresql",
        parser=standard_parser,
        normalizer=string_name_normalizer,
        aliases=("yugabyte", "yugabytedb"),
    ),
    BackendDefinition(
        engine="django_mongodb_backend",
        parser=mongodb_parser,
        normalizer=mongodb_normalizer,
        aliases=("mongo", "mongodb"),
    ),
)
