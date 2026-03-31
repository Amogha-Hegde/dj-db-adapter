from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from dj_db_adapter import config
from dj_db_adapter import databases
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


def test_databases_support_multiple_aliases_from_env_urls() -> None:
    os.environ["DJANGO_DATABASE_ALIASES"] = "default,analytics"
    os.environ["DJANGO_DATABASE_DEFAULT_URL"] = "postgres://app:secret@db.example.com:5432/main"
    os.environ["DJANGO_DATABASE_ANALYTICS_URL"] = "mysql://report:secret@mysql.example.com:3306/warehouse"

    loaded = databases()

    assert set(loaded) == {"default", "analytics"}
    assert loaded["default"]["ENGINE"] == "django.db.backends.postgresql"
    assert loaded["default"]["NAME"] == "main"
    assert loaded["analytics"]["ENGINE"] == "django.db.backends.mysql"
    assert loaded["analytics"]["HOST"] == "mysql.example.com"


def test_default_alias_supports_sqlite_name_from_env(tmp_path: Path) -> None:
    os.environ["DJANGO_DATABASE_DEFAULT_NAME"] = str(tmp_path / "custom.sqlite3")

    loaded = config(base_dir=tmp_path)

    assert loaded["ENGINE"] == "django.db.backends.sqlite3"
    assert loaded["NAME"] == tmp_path / "custom.sqlite3"


def test_json_config_file_per_alias(tmp_path: Path) -> None:
    config_file = tmp_path / "analytics.json"
    config_file.write_text(
        json.dumps(
            {
                "ENGINE": "snowflake",
                "NAME": "warehouse",
                "USER": "reporter",
                "PASSWORD": "secret",
                "ACCOUNT": "account-1",
                "SCHEMA": "PUBLIC",
                "WAREHOUSE": "COMPUTE_WH",
                "ROLE": "ANALYST",
            }
        ),
        encoding="utf-8",
    )
    os.environ["DJANGO_DATABASE_ANALYTICS_CONFIG_FILE"] = str(config_file)

    loaded = config("analytics")

    assert loaded["ENGINE"] == "django_snowflake"
    assert loaded["ACCOUNT"] == "account-1"
    assert loaded["WAREHOUSE"] == "COMPUTE_WH"


def test_ini_config_file_per_alias(tmp_path: Path) -> None:
    config_file = tmp_path / "archive.ini"
    config_file.write_text(
        "\n".join(
            [
                "[database]",
                "engine = postgres",
                "name = archive",
                "user = archiver",
                "password = secret",
                "host = pg.example.com",
                "port = 5432",
                "",
                "[options]",
                "sslmode = require",
                "",
                "[test]",
                "name = archive_test",
            ]
        ),
        encoding="utf-8",
    )
    os.environ["DJANGO_DATABASE_ARCHIVE_CONFIG_FILE"] = str(config_file)

    loaded = config("archive")

    assert loaded["ENGINE"] == "django.db.backends.postgresql"
    assert loaded["OPTIONS"] == {"sslmode": "require"}
    assert loaded["TEST"] == {"NAME": "archive_test"}


def test_yaml_config_file_per_alias(tmp_path: Path) -> None:
    config_file = tmp_path / "mongo.yaml"
    config_file.write_text(
        "\n".join(
            [
                "engine: mongodb",
                "name: analytics",
                "host: mongodb://mongo.example.com:27017/analytics",
            ]
        ),
        encoding="utf-8",
    )
    os.environ["DJANGO_DATABASE_MONGO_CONFIG_FILE"] = str(config_file)

    loaded = config("mongo")

    assert loaded["ENGINE"] == "django_mongodb_backend"
    assert loaded["HOST"] == "mongodb://mongo.example.com:27017/analytics"


def test_alias_specific_env_overrides_file_config(tmp_path: Path) -> None:
    config_file = tmp_path / "analytics.json"
    config_file.write_text(
        json.dumps(
            {
                "ENGINE": "postgres",
                "NAME": "warehouse",
                "HOST": "old.example.com",
                "USER": "reporter",
            }
        ),
        encoding="utf-8",
    )
    os.environ["DJANGO_DATABASE_ANALYTICS_CONFIG_FILE"] = str(config_file)
    os.environ["DJANGO_DATABASE_ANALYTICS_HOST"] = "new.example.com"
    os.environ["DJANGO_DATABASE_ANALYTICS_OPTIONS"] = '{"sslmode": "require"}'

    loaded = config("analytics")

    assert loaded["HOST"] == "new.example.com"
    assert loaded["OPTIONS"] == {"sslmode": "require"}


def test_oracle_standard_connect_env_shape() -> None:
    os.environ["DJANGO_DATABASE_ORACLE_TENANT_ENGINE"] = "oracle"
    os.environ["DJANGO_DATABASE_ORACLE_TENANT_HOST"] = "oracle.example.com"
    os.environ["DJANGO_DATABASE_ORACLE_TENANT_PORT"] = "1521"
    os.environ["DJANGO_DATABASE_ORACLE_TENANT_NAME"] = "ORCLCDB"
    os.environ["DJANGO_DATABASE_ORACLE_TENANT_USER"] = "scott"
    os.environ["DJANGO_DATABASE_ORACLE_TENANT_PASSWORD"] = "tiger"

    loaded = config("oracle_tenant")

    assert loaded["ENGINE"] == "django.db.backends.oracle"
    assert loaded["HOST"] == "oracle.example.com"
    assert loaded["PORT"] == "1521"
    assert loaded["NAME"] == "ORCLCDB"
    assert loaded["OPTIONS"] == {"threaded": True}


def test_oracle_easy_connect_shape_defaults_threaded_option() -> None:
    os.environ["DJANGO_DATABASE_REPORTING_ENGINE"] = "oracle"
    os.environ["DJANGO_DATABASE_REPORTING_NAME"] = "dbhost.example.com:1521/ORCLPDB1"
    os.environ["DJANGO_DATABASE_REPORTING_USER"] = "reporter"
    os.environ["DJANGO_DATABASE_REPORTING_PASSWORD"] = "secret"

    loaded = config("reporting")

    assert loaded["ENGINE"] == "django.db.backends.oracle"
    assert loaded["NAME"] == "dbhost.example.com:1521/ORCLPDB1"
    assert loaded["OPTIONS"] == {"threaded": True}


def test_oracle_full_connect_descriptor_shape() -> None:
    os.environ["DJANGO_DATABASE_WAREHOUSE_ENGINE"] = "oracle"
    os.environ["DJANGO_DATABASE_WAREHOUSE_PROTOCOL"] = "tcp"
    os.environ["DJANGO_DATABASE_WAREHOUSE_HOST"] = "oracle.example.com"
    os.environ["DJANGO_DATABASE_WAREHOUSE_PORT"] = "1521"
    os.environ["DJANGO_DATABASE_WAREHOUSE_SERVICE_NAME"] = "ORCLPDB1"
    os.environ["DJANGO_DATABASE_WAREHOUSE_USER"] = "warehouse"
    os.environ["DJANGO_DATABASE_WAREHOUSE_PASSWORD"] = "secret"

    loaded = config("warehouse")

    assert loaded["ENGINE"] == "django.db.backends.oracle"
    assert loaded["NAME"] == (
        "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=oracle.example.com)(PORT=1521))"
        "(CONNECT_DATA=(SERVICE_NAME=ORCLPDB1)))"
    )
    assert "HOST" not in loaded
    assert "PORT" not in loaded
    assert loaded["OPTIONS"] == {"threaded": True}


def test_invalid_backend_specific_setting_raises(tmp_path: Path) -> None:
    config_file = tmp_path / "broken.json"
    config_file.write_text(
        json.dumps(
            {
                "ENGINE": "postgres",
                "NAME": "main",
                "WAREHOUSE": "NOT_ALLOWED",
            }
        ),
        encoding="utf-8",
    )
    os.environ["DJANGO_DATABASE_DEFAULT_CONFIG_FILE"] = str(config_file)

    with pytest.raises(ValueError, match="unsupported settings"):
        config()


def test_custom_backend_registration() -> None:
    register_backend(
        "customdb",
        "vendor.backend",
        env_map=(("NAME", "NAME"),),
        settings={"NAME"},
    )
    os.environ["DJANGO_DATABASE_CUSTOM_NAME"] = "custom_name"
    os.environ["DJANGO_DATABASE_CUSTOM_ENGINE"] = "customdb"

    loaded = config("custom")

    assert loaded["ENGINE"] == "vendor.backend"
    assert loaded["NAME"] == "custom_name"


def test_read_setting_prefers_direct_env(tmp_path: Path) -> None:
    value_file = tmp_path / "value.txt"
    value_file.write_text("from-file", encoding="utf-8")
    os.environ["EXAMPLE_FILE"] = str(value_file)
    os.environ["EXAMPLE"] = "from-env"

    assert read_setting("EXAMPLE") == "from-env"
