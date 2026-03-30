from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from dj_db_adapter import config
from dj_db_adapter import parse
from dj_db_adapter import read_setting
from dj_db_adapter import register_backend


@pytest.fixture(autouse=True)
def clean_environment():
    original_environ = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_environ)


def test_parse_postgres_url() -> None:
    parsed = parse("postgres://user:pass@db.example.com:5432/app?sslmode=require")
    assert parsed["ENGINE"] == "django.db.backends.postgresql"
    assert parsed["NAME"] == "app"
    assert parsed["HOST"] == "db.example.com"
    assert parsed["PORT"] == 5432
    assert parsed["OPTIONS"] == {"sslmode": "require"}


def test_config_supports_file_backed_values() -> None:
    with tempfile.TemporaryDirectory() as tempdir:
        secret_file = Path(tempdir) / "database_url.txt"
        secret_file.write_text("mysql://user:pass@mysql.example.com:3306/sample", encoding="utf-8")
        os.environ["DATABASE_URL_FILE"] = str(secret_file)

        loaded = config()

    assert loaded["ENGINE"] == "django.db.backends.mysql"
    assert loaded["NAME"] == "sample"
    assert loaded["HOST"] == "mysql.example.com"


def test_env_overrides_url_config() -> None:
    os.environ["DATABASE_URL"] = "postgres://user:pass@db.example.com:5432/sample"
    os.environ["DJANGO_DB_NAME"] = "override"
    os.environ["DJANGO_DB_OPTIONS"] = '{"sslmode": "require"}'
    os.environ["DJANGO_DB_CONN_HEALTH_CHECKS"] = "true"

    loaded = config()

    assert loaded["NAME"] == "override"
    assert loaded["OPTIONS"] == {"sslmode": "require"}
    assert loaded["CONN_HEALTH_CHECKS"] is True


def test_sqlite_defaults_to_path() -> None:
    loaded = config(base_dir="/tmp/example")
    assert loaded["ENGINE"] == "django.db.backends.sqlite3"
    assert loaded["NAME"] == Path("/tmp/example/db.sqlite3")


def test_custom_backend_registration() -> None:
    register_backend("customdb", "vendor.backend")
    loaded = parse("customdb://user:pass@db.example.com:9999/name")
    assert loaded["ENGINE"] == "vendor.backend"


def test_read_setting_prefers_direct_env() -> None:
    with tempfile.TemporaryDirectory() as tempdir:
        value_file = Path(tempdir) / "value.txt"
        value_file.write_text("from-file", encoding="utf-8")
        os.environ["EXAMPLE_FILE"] = str(value_file)
        os.environ["EXAMPLE"] = "from-env"
        assert read_setting("EXAMPLE") == "from-env"
