from __future__ import annotations

from urllib.parse import urlparse

from dj_db_adapter.backends.base import BackendDefinition
from dj_db_adapter.backends.base import COMMON_SETTINGS
from dj_db_adapter.backends.base import DatabaseConfig
from dj_db_adapter.backends.base import standard_parser
from dj_db_adapter.backends.cockroach import BACKEND as COCKROACH
from dj_db_adapter.backends.firebird import BACKEND as FIREBIRD
from dj_db_adapter.backends.mongodb import BACKEND as MONGODB
from dj_db_adapter.backends.mssql import BACKEND as MSSQL
from dj_db_adapter.backends.mysql import BACKEND as MYSQL
from dj_db_adapter.backends.oracle import BACKEND as ORACLE
from dj_db_adapter.backends.postgresql import BACKEND as POSTGRESQL
from dj_db_adapter.backends.snowflake import BACKEND as SNOWFLAKE
from dj_db_adapter.backends.spanner import BACKEND as SPANNER
from dj_db_adapter.backends.sqlite import BACKEND as SQLITE
from dj_db_adapter.backends.tidb import BACKEND as TIDB
from dj_db_adapter.backends.yugabyte import BACKEND as YUGABYTE

REGISTERED_BACKENDS: tuple[BackendDefinition, ...] = (
    SQLITE,
    POSTGRESQL,
    MYSQL,
    ORACLE,
    COCKROACH,
    FIREBIRD,
    SPANNER,
    MSSQL,
    SNOWFLAKE,
    TIDB,
    YUGABYTE,
    MONGODB,
)

_BACKEND_REGISTRY: dict[str, BackendDefinition] = {}


def _load_default_backends() -> None:
    if _BACKEND_REGISTRY:
        return
    for backend in REGISTERED_BACKENDS:
        for alias in backend.aliases:
            _BACKEND_REGISTRY[alias.lower()] = backend
        _BACKEND_REGISTRY[backend.engine.lower()] = backend


def register_backend(
    alias: str,
    engine: str,
    *,
    parser=standard_parser,
    normalizer=None,
    env_map=(),
    settings=frozenset(),
) -> None:
    _load_default_backends()
    definition = BackendDefinition(
        engine=engine,
        parser=parser,
        aliases=(alias.lower(), engine.lower()),
        env_map=tuple(env_map),
        settings=frozenset(COMMON_SETTINGS | set(settings)),
        normalizer=normalizer,
    )
    _BACKEND_REGISTRY[alias.lower()] = definition
    _BACKEND_REGISTRY[engine.lower()] = definition


def resolve_backend(value: str | None) -> BackendDefinition | None:
    _load_default_backends()
    if value is None:
        return None
    return _BACKEND_REGISTRY.get(value.lower())


def parse_database_url(url: str) -> DatabaseConfig:
    parsed = urlparse(url)
    if not parsed.scheme:
        raise ValueError("Database URL is missing a scheme")
    backend = resolve_backend(parsed.scheme)
    if backend is None:
        return standard_parser(parsed, parsed.scheme)
    return backend.parser(parsed, backend.engine)


def normalize_database_config(config: DatabaseConfig) -> DatabaseConfig:
    engine = str(config.get("ENGINE", ""))
    backend = resolve_backend(engine)
    if backend is None or backend.normalizer is None:
        return dict(config)
    return backend.normalizer(config)
