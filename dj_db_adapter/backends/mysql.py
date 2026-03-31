from __future__ import annotations

from dj_db_adapter.backends.base import BackendDefinition
from dj_db_adapter.backends.base import base_settings
from dj_db_adapter.backends.base import standard_parser
from dj_db_adapter.backends.base import string_name_normalizer

BACKEND = BackendDefinition(
    engine="django.db.backends.mysql",
    parser=standard_parser,
    aliases=("mysql", "mariadb", "django.db.backends.mysql"),
    env_prefix="MYSQL",
    env_map=(
        ("NAME", "NAME"),
        ("USER", "USER"),
        ("PASSWORD", "PASSWORD"),
        ("HOST", "HOST"),
        ("PORT", "PORT"),
    ),
    settings=base_settings("HOST", "NAME", "PASSWORD", "PORT", "USER"),
    normalizer=string_name_normalizer,
)
