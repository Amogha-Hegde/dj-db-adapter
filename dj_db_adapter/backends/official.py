from __future__ import annotations

from dj_db_adapter.backends.base import BackendDefinition
from dj_db_adapter.backends.base import sqlite_normalizer
from dj_db_adapter.backends.base import sqlite_parser
from dj_db_adapter.backends.base import standard_parser
from dj_db_adapter.backends.base import string_name_normalizer


OFFICIAL_BACKENDS: tuple[BackendDefinition, ...] = (
    BackendDefinition(
        engine="django.db.backends.sqlite3",
        parser=sqlite_parser,
        normalizer=sqlite_normalizer,
        aliases=("sqlite", "sqlite3"),
    ),
    BackendDefinition(
        engine="django.db.backends.postgresql",
        parser=standard_parser,
        normalizer=string_name_normalizer,
        aliases=("postgres", "postgresql", "pgsql", "psql"),
    ),
    BackendDefinition(
        engine="django.db.backends.mysql",
        parser=standard_parser,
        normalizer=string_name_normalizer,
        aliases=("mysql", "mariadb"),
    ),
    BackendDefinition(
        engine="django.db.backends.oracle",
        parser=standard_parser,
        normalizer=string_name_normalizer,
        aliases=("oracle", "oracledb"),
    ),
)
