from __future__ import annotations

from urllib.parse import urlparse

from dj_db_adapter.backends.base import BackendDefinition
from dj_db_adapter.backends.base import DatabaseConfig
from dj_db_adapter.backends.base import standard_parser
from dj_db_adapter.backends.official import OFFICIAL_BACKENDS
from dj_db_adapter.backends.thirdparty import THIRD_PARTY_BACKENDS

_BACKEND_REGISTRY: dict[str, BackendDefinition] = {}


def register_backend(
    alias: str,
    engine: str,
    *,
    parser=standard_parser,
    normalizer=None,
) -> None:
    definition = BackendDefinition(
        engine=engine,
        parser=parser,
        normalizer=normalizer,
        aliases=(alias.lower(),),
    )
    _BACKEND_REGISTRY[alias.lower()] = definition
    _BACKEND_REGISTRY[engine.lower()] = definition


def load_default_backends() -> None:
    if _BACKEND_REGISTRY:
        return

    for backend in (*OFFICIAL_BACKENDS, *THIRD_PARTY_BACKENDS):
        for alias in backend.aliases:
            _BACKEND_REGISTRY[alias.lower()] = backend
        _BACKEND_REGISTRY[backend.engine.lower()] = backend


def resolve_backend(value: str | None) -> BackendDefinition | None:
    load_default_backends()
    if value is None:
        return None
    lowered = value.lower()
    if lowered in _BACKEND_REGISTRY:
        return _BACKEND_REGISTRY[lowered]
    return BackendDefinition(engine=value, parser=standard_parser)


def parse_database_url(url: str) -> DatabaseConfig:
    parsed = urlparse(url)
    if not parsed.scheme:
        raise ValueError("DATABASE_URL is missing a database scheme")

    backend = resolve_backend(parsed.scheme)
    if backend is None:
        raise ValueError(f"Unsupported database backend: {parsed.scheme}")
    return backend.parser(parsed, backend.engine)


def normalize_database_config(config: DatabaseConfig) -> DatabaseConfig:
    backend = resolve_backend(str(config.get("ENGINE")))
    if backend is None or backend.normalizer is None:
        return dict(config)
    return backend.normalizer(config)
