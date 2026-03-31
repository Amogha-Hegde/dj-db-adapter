from __future__ import annotations

from dj_db_adapter.backends.base import BackendDefinition
from dj_db_adapter.backends.base import DatabaseConfig
from dj_db_adapter.backends.base import base_settings
from dj_db_adapter.backends.base import string_name_normalizer


def mongodb_parser(parsed, engine: str) -> DatabaseConfig:
    return {
        "ENGINE": engine,
        "HOST": parsed.geturl(),
        "NAME": parsed.path.lstrip("/"),
    }


def mongodb_normalizer(config: DatabaseConfig) -> DatabaseConfig:
    normalized = string_name_normalizer(config)
    normalized.pop("PORT", None)
    return normalized


BACKEND = BackendDefinition(
    engine="django_mongodb_backend",
    parser=mongodb_parser,
    aliases=("mongo", "mongodb", "django_mongodb_backend"),
    env_prefix="MONGODB",
    env_map=(
        ("NAME", "NAME"),
        ("HOST", "HOST"),
    ),
    settings=base_settings("HOST", "NAME"),
    normalizer=mongodb_normalizer,
)
