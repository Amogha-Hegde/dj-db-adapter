from __future__ import annotations

from dj_db_adapter.backends.base import BackendDefinition
from dj_db_adapter.backends.base import base_settings
from dj_db_adapter.backends.base import standard_parser
from dj_db_adapter.backends.base import string_name_normalizer

ALLOWED_PG_OPTIONS = frozenset(
    {
        "search_path",
        "application_name",
        "statement_timeout",
        "lock_timeout",
        "idle_in_transaction_session_timeout",
        "deadlock_timeout",
        "default_transaction_isolation",
        "default_transaction_read_only",
        "default_transaction_deferrable",
        "jit",
        "max_parallel_workers_per_gather",
        "work_mem",
        "maintenance_work_mem",
        "random_page_cost",
        "effective_cache_size",
        "log_min_duration_statement",
        "TimeZone",
        "DateStyle",
        "row_security",
    }
)

BACKEND = BackendDefinition(
    engine="django.db.backends.postgresql",
    parser=standard_parser,
    aliases=("postgres", "postgresql", "pgsql", "psql", "django.db.backends.postgresql"),
    env_prefix="POSTGRES",
    env_map=(
        ("NAME", "NAME"),
        ("USER", "USER"),
        ("PASSWORD", "PASSWORD"),
        ("HOST", "HOST"),
        ("PORT", "PORT"),
    ),
    settings=base_settings("HOST", "NAME", "PASSWORD", "PORT", "USER"),
    allowed_options=ALLOWED_PG_OPTIONS,
    normalizer=string_name_normalizer,
)
