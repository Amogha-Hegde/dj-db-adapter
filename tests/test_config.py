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


def test_databases_support_multiple_aliases_from_urls() -> None:
    os.environ["DJ_DB_ALIASES"] = "default,analytics"
    os.environ["DJ_DB_DEFAULT_URL"] = "postgres://app:secret@db.example.com:5432/main"
    os.environ["DJ_DB_ANALYTICS_URL"] = "mysql://report:secret@mysql.example.com:3306/warehouse"

    loaded = databases()

    assert set(loaded) == {"default", "analytics"}
    assert loaded["default"]["ENGINE"] == "django.db.backends.postgresql"
    assert loaded["default"]["NAME"] == "main"
    assert loaded["analytics"]["ENGINE"] == "django.db.backends.mysql"
    assert loaded["analytics"]["HOST"] == "mysql.example.com"


def test_databases_is_empty_when_no_database_env_is_set() -> None:
    assert databases() == {}


def test_config_raises_when_alias_is_not_configured() -> None:
    with pytest.raises(ValueError, match="requires BACKEND, ENGINE, URL, or CONFIG_FILE"):
        config()


def test_postgres_backend_specific_env_shape() -> None:
    os.environ["DJ_DB_DEFAULT_BACKEND"] = "postgres"
    os.environ["DJ_DB_DEFAULT_POSTGRES_USER"] = "app"
    os.environ["DJ_DB_DEFAULT_POSTGRES_NAME"] = "main"
    os.environ["DJ_DB_DEFAULT_POSTGRES_HOST"] = "db.example.com"
    os.environ["DJ_DB_DEFAULT_POSTGRES_PORT"] = "5432"
    os.environ["DJ_DB_DEFAULT_POSTGRES_PASSWORD"] = "secret"
    os.environ["DJ_DB_DEFAULT_POSTGRES_CONN_MAX_AGE"] = "120"
    os.environ["DJ_DB_DEFAULT_POSTGRES_CONN_HEALTH_CHECKS"] = "true"
    os.environ["DJ_DB_DEFAULT_POSTGRES_AUTOCOMMIT"] = "false"

    loaded = config()

    assert loaded["ENGINE"] == "django.db.backends.postgresql"
    assert loaded["USER"] == "app"
    assert loaded["NAME"] == "main"
    assert loaded["HOST"] == "db.example.com"
    assert loaded["PORT"] == "5432"
    assert loaded["PASSWORD"] == "secret"
    assert loaded["CONN_MAX_AGE"] == 120
    assert loaded["CONN_HEALTH_CHECKS"] is True
    assert loaded["AUTOCOMMIT"] is False


def test_postgres_allowed_options_are_loaded() -> None:
    os.environ["DJ_DB_DEFAULT_BACKEND"] = "postgres"
    os.environ["DJ_DB_DEFAULT_POSTGRES_NAME"] = "main"
    os.environ["DJ_DB_DEFAULT_POSTGRES_USER"] = "app"
    os.environ["DJ_DB_DEFAULT_POSTGRES__OPTIONS__APPLICATION_NAME"] = "api"
    os.environ["DJ_DB_DEFAULT_POSTGRES__OPTIONS__SEARCH_PATH"] = "public,tenant"

    loaded = config()

    assert loaded["OPTIONS"] == {
        "application_name": "api",
        "search_path": "public,tenant",
    }


def test_postgres_invalid_option_is_rejected() -> None:
    os.environ["DJ_DB_DEFAULT_BACKEND"] = "postgres"
    os.environ["DJ_DB_DEFAULT_POSTGRES_NAME"] = "main"
    os.environ["DJ_DB_DEFAULT_POSTGRES__OPTIONS__BAD_OPTION"] = "1"

    with pytest.raises(ValueError, match="unsupported option"):
        config()


def test_engine_override_wins_over_backend_alias() -> None:
    os.environ["DJ_DB_DEFAULT_BACKEND"] = "postgres"
    os.environ["DJ_DB_DEFAULT_ENGINE"] = "django.db.backends.mysql"
    os.environ["DJ_DB_DEFAULT_URL"] = "postgres://app:secret@db.example.com:5432/main"

    loaded = config()

    assert loaded["ENGINE"] == "django.db.backends.mysql"


def test_json_config_file_per_alias(tmp_path: Path) -> None:
    config_file = tmp_path / "analytics.json"
    config_file.write_text(
        json.dumps(
            {
                "BACKEND": "snowflake",
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
    os.environ["DJ_DB_ANALYTICS_CONFIG_FILE"] = str(config_file)

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
                "backend = postgres",
                "name = archive",
                "user = archiver",
                "password = secret",
                "host = pg.example.com",
                "port = 5432",
                "",
                "[options]",
                "application_name = archive-worker",
            ]
        ),
        encoding="utf-8",
    )
    os.environ["DJ_DB_ARCHIVE_CONFIG_FILE"] = str(config_file)

    loaded = config("archive")

    assert loaded["ENGINE"] == "django.db.backends.postgresql"
    assert loaded["OPTIONS"] == {"application_name": "archive-worker"}


def test_oracle_standard_connect_env_shape() -> None:
    os.environ["DJ_DB_ORACLE_TENANT_BACKEND"] = "oracle"
    os.environ["DJ_DB_ORACLE_TENANT_ORACLE_HOST"] = "oracle.example.com"
    os.environ["DJ_DB_ORACLE_TENANT_ORACLE_PORT"] = "1521"
    os.environ["DJ_DB_ORACLE_TENANT_ORACLE_NAME"] = "ORCLCDB"
    os.environ["DJ_DB_ORACLE_TENANT_ORACLE_USER"] = "scott"
    os.environ["DJ_DB_ORACLE_TENANT_ORACLE_PASSWORD"] = "tiger"

    loaded = config("oracle_tenant")

    assert loaded["ENGINE"] == "django.db.backends.oracle"
    assert loaded["HOST"] == "oracle.example.com"
    assert loaded["PORT"] == "1521"
    assert loaded["NAME"] == "ORCLCDB"
    assert loaded["OPTIONS"] == {"threaded": True}


def test_oracle_full_connect_descriptor_shape() -> None:
    os.environ["DJ_DB_WAREHOUSE_BACKEND"] = "oracle"
    os.environ["DJ_DB_WAREHOUSE_ORACLE_PROTOCOL"] = "tcp"
    os.environ["DJ_DB_WAREHOUSE_ORACLE_HOST"] = "oracle.example.com"
    os.environ["DJ_DB_WAREHOUSE_ORACLE_PORT"] = "1521"
    os.environ["DJ_DB_WAREHOUSE_ORACLE_SERVICE_NAME"] = "ORCLPDB1"
    os.environ["DJ_DB_WAREHOUSE_ORACLE_USER"] = "warehouse"
    os.environ["DJ_DB_WAREHOUSE_ORACLE_PASSWORD"] = "secret"

    loaded = config("warehouse")

    assert loaded["ENGINE"] == "django.db.backends.oracle"
    assert loaded["NAME"] == (
        "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=oracle.example.com)(PORT=1521))"
        "(CONNECT_DATA=(SERVICE_NAME=ORCLPDB1)))"
    )
    assert "HOST" not in loaded
    assert "PORT" not in loaded
    assert loaded["OPTIONS"] == {"threaded": True}


def test_yaml_config_file_is_rejected(tmp_path: Path) -> None:
    config_file = tmp_path / "mongo.yaml"
    config_file.write_text("engine: mongodb\n", encoding="utf-8")
    os.environ["DJ_DB_MONGO_CONFIG_FILE"] = str(config_file)

    with pytest.raises(ValueError, match="Unsupported config file format"):
        config("mongo")


def test_custom_backend_registration() -> None:
    register_backend(
        "customdb",
        "vendor.backend",
        env_prefix="CUSTOMDB",
        env_map=(("NAME", "NAME"),),
        settings={"NAME"},
    )
    os.environ["DJ_DB_CUSTOM_BACKEND"] = "customdb"
    os.environ["DJ_DB_CUSTOM_CUSTOMDB_NAME"] = "custom_name"

    loaded = config("custom")

    assert loaded["ENGINE"] == "vendor.backend"
    assert loaded["NAME"] == "custom_name"


def test_read_setting_prefers_direct_env(tmp_path: Path) -> None:
    value_file = tmp_path / "value.txt"
    value_file.write_text("from-file", encoding="utf-8")
    os.environ["EXAMPLE_FILE"] = str(value_file)
    os.environ["EXAMPLE"] = "from-env"

    assert read_setting("EXAMPLE") == "from-env"
