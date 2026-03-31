from __future__ import annotations

from dj_db_adapter.backends.base import DatabaseConfig
from dj_db_adapter.backends.base import BackendDefinition
from dj_db_adapter.backends.base import base_settings
from dj_db_adapter.backends.base import standard_parser
from dj_db_adapter.backends.base import string_name_normalizer


def oracle_normalizer(config: DatabaseConfig) -> DatabaseConfig:
    normalized = string_name_normalizer(config)

    options = dict(normalized.get("OPTIONS", {}))
    options.setdefault("threaded", True)
    normalized["OPTIONS"] = options

    protocol = str(normalized.pop("PROTOCOL", "TCP") or "TCP").upper()
    service_name = normalized.pop("SERVICE_NAME", None)
    host = normalized.get("HOST")
    port = normalized.get("PORT")
    if service_name:
        normalized["NAME"] = (
            f"(DESCRIPTION=(ADDRESS=(PROTOCOL={protocol})(HOST={host})(PORT={port}))"
            f"(CONNECT_DATA=(SERVICE_NAME={service_name})))"
        )
        normalized.pop("HOST", None)
        normalized.pop("PORT", None)

    return normalized


BACKEND = BackendDefinition(
    engine="django.db.backends.oracle",
    parser=standard_parser,
    aliases=("oracle", "oracledb", "django.db.backends.oracle"),
    env_map=(
        ("NAME", "NAME"),
        ("USER", "USER"),
        ("PASSWORD", "PASSWORD"),
        ("HOST", "HOST"),
        ("PORT", "PORT"),
        ("PROTOCOL", "PROTOCOL"),
        ("SERVICE_NAME", "SERVICE_NAME"),
    ),
    settings=base_settings("HOST", "NAME", "PASSWORD", "PORT", "PROTOCOL", "SERVICE_NAME", "USER"),
    normalizer=oracle_normalizer,
)
