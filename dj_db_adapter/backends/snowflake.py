from __future__ import annotations

from urllib.parse import unquote

from dj_db_adapter.backends.base import BackendDefinition
from dj_db_adapter.backends.base import DatabaseConfig
from dj_db_adapter.backends.base import base_settings
from dj_db_adapter.backends.base import query_options
from dj_db_adapter.backends.base import string_name_normalizer


def snowflake_parser(parsed, engine: str) -> DatabaseConfig:
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


BACKEND = BackendDefinition(
    engine="django_snowflake",
    parser=snowflake_parser,
    aliases=("snowflake", "django_snowflake"),
    env_prefix="SNOWFLAKE",
    env_map=(
        ("NAME", "NAME"),
        ("USER", "USER"),
        ("PASSWORD", "PASSWORD"),
        ("ACCOUNT", "ACCOUNT"),
        ("SCHEMA", "SCHEMA"),
        ("WAREHOUSE", "WAREHOUSE"),
        ("ROLE", "ROLE"),
    ),
    settings=base_settings("ACCOUNT", "NAME", "PASSWORD", "ROLE", "SCHEMA", "USER", "WAREHOUSE"),
    normalizer=string_name_normalizer,
)
