from __future__ import annotations

from dj_db_adapter.backends.base import BackendDefinition
from dj_db_adapter.backends.base import base_settings
from dj_db_adapter.backends.base import sqlite_normalizer
from dj_db_adapter.backends.base import sqlite_parser

BACKEND = BackendDefinition(
    engine="django.db.backends.sqlite3",
    parser=sqlite_parser,
    aliases=("sqlite", "sqlite3", "django.db.backends.sqlite3"),
    env_prefix="SQLITE",
    env_map=(("NAME", "NAME"),),
    settings=base_settings("NAME"),
    normalizer=sqlite_normalizer,
    default_name="db.sqlite3",
)
