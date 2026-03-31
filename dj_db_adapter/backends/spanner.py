from __future__ import annotations

from dj_db_adapter.backends.base import BackendDefinition
from dj_db_adapter.backends.base import DatabaseConfig
from dj_db_adapter.backends.base import base_settings
from dj_db_adapter.backends.base import query_options
from dj_db_adapter.backends.base import string_name_normalizer


def spanner_parser(parsed, engine: str) -> DatabaseConfig:
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


BACKEND = BackendDefinition(
    engine="django_spanner",
    parser=spanner_parser,
    aliases=("google-cloud-spanner", "spanner", "django_spanner"),
    env_map=(
        ("PROJECT", "PROJECT"),
        ("INSTANCE", "INSTANCE"),
        ("NAME", "NAME"),
    ),
    settings=base_settings("INSTANCE", "NAME", "PROJECT"),
    normalizer=string_name_normalizer,
)
