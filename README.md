# dj-db-adapter

`dj-db-adapter` is a Django database configuration helper built around environment-first configuration.

It provides:

- alias-based database configuration
- backend-aware env var parsing
- URL-based configuration
- JSON and INI config file support
- strict backend-specific setting validation
- support for configuring multiple Django database aliases at once

The library is designed for projects that want predictable, explicit database configuration without embedding parsing logic in Django settings files.

## Installation

```bash
pip install dj-db-adapter
```

## Quick Start

```python
from dj_db_adapter import databases

DATABASES = databases()
```

If no database-related env vars are set, `databases()` returns `{}`.

## Configuration Model

Each database alias is configured using the `DJ_DB_<ALIAS>_*` pattern.

Top-level variables:

```text
DJ_DB_<ALIAS>_BACKEND=
DJ_DB_<ALIAS>_ENGINE=
DJ_DB_<ALIAS>_URL=
DJ_DB_<ALIAS>_CONFIG_FILE=
```

Resolution order:

1. `BACKEND`
2. `ENGINE`
3. `URL`
4. `CONFIG_FILE`
5. backend-specific env vars

`BACKEND` selects a built-in backend and resolves the Django engine automatically.

`ENGINE` is only needed when you want to override the resolved engine explicitly.

## Public API

### `databases(aliases=None)`

Returns a Django `DATABASES` mapping.

If `aliases` is omitted, the library reads:

```text
DJ_DB_ALIASES=default,analytics,archive
```

If `DJ_DB_ALIASES` is not set, no aliases are assumed.

### `config(alias="default")`

Returns the config for one alias.

If the alias is not configured, `ValueError` is raised.

### `parse(url)`

Parses a single database URL into a Django database config dictionary.

### `register_backend(alias, engine, ...)`

Registers a custom backend alias.

## Multiple Aliases

Example:

```bash
export DJ_DB_ALIASES=default,analytics

export DJ_DB_DEFAULT_BACKEND=postgres
export DJ_DB_DEFAULT_POSTGRES_NAME=app_db
export DJ_DB_DEFAULT_POSTGRES_USER=app_user
export DJ_DB_DEFAULT_POSTGRES_PASSWORD=change-me
export DJ_DB_DEFAULT_POSTGRES_HOST=postgres.example.com
export DJ_DB_DEFAULT_POSTGRES_PORT=5432

export DJ_DB_ANALYTICS_URL=mysql://report:change-me@mysql.example.com:3306/analytics
```

```python
from dj_db_adapter import databases

DATABASES = databases()
```

## URL-Based Configuration

You can configure any alias with a database URL:

```bash
export DJ_DB_DEFAULT_URL=postgres://app_user:change-me@postgres.example.com:5432/app_db
export DJ_DB_ANALYTICS_URL=mysql://report:change-me@mysql.example.com:3306/analytics
```

The URL scheme is mapped to the correct Django engine where supported.

## Config File Support

An alias can also be configured with:

```text
DJ_DB_<ALIAS>_CONFIG_FILE=
```

Supported formats:

- `.json`
- `.ini`
- `.cfg`

### JSON Example

```json
{
  "BACKEND": "postgres",
  "NAME": "app_db",
  "USER": "app_user",
  "PASSWORD": "change-me",
  "HOST": "postgres.example.com",
  "PORT": 5432
}
```

### INI Example

```ini
[database]
backend = postgres
name = app_db
user = app_user
password = change-me
host = postgres.example.com
port = 5432

[options]
application_name = django-app
```

INI mapping rules:

- `[database]` maps to the main database config
- `[options]` maps to `OPTIONS`
- `[test]` maps to `TEST`

## PostgreSQL Configuration

When:

```text
DJ_DB_<ALIAS>_BACKEND=postgres
```

the library reads PostgreSQL-specific values from:

```text
DJ_DB_<ALIAS>_POSTGRES_USER=
DJ_DB_<ALIAS>_POSTGRES_NAME=
DJ_DB_<ALIAS>_POSTGRES_HOST=
DJ_DB_<ALIAS>_POSTGRES_PORT=
DJ_DB_<ALIAS>_POSTGRES_PASSWORD=
```

Supported common connection settings:

```text
DJ_DB_<ALIAS>_POSTGRES_CONN_MAX_AGE=
DJ_DB_<ALIAS>_POSTGRES_CONN_HEALTH_CHECKS=
DJ_DB_<ALIAS>_POSTGRES_AUTOCOMMIT=
DJ_DB_<ALIAS>_POSTGRES_ATOMIC_REQUESTS=
DJ_DB_<ALIAS>_POSTGRES_DISABLE_SERVER_SIDE_CURSORS=
```

### PostgreSQL `OPTIONS`

Options are passed through env vars using:

```text
DJ_DB_<ALIAS>_POSTGRES__OPTIONS__<OPTION_NAME>=
```

Example:

```bash
export DJ_DB_DEFAULT_POSTGRES__OPTIONS__APPLICATION_NAME=api
export DJ_DB_DEFAULT_POSTGRES__OPTIONS__SEARCH_PATH=public
```

Allowed PostgreSQL option names:

- `search_path`
- `application_name`
- `statement_timeout`
- `lock_timeout`
- `idle_in_transaction_session_timeout`
- `deadlock_timeout`
- `default_transaction_isolation`
- `default_transaction_read_only`
- `default_transaction_deferrable`
- `jit`
- `max_parallel_workers_per_gather`
- `work_mem`
- `maintenance_work_mem`
- `random_page_cost`
- `effective_cache_size`
- `log_min_duration_statement`
- `TimeZone`
- `DateStyle`
- `row_security`

Unsupported option names raise `ValueError`.

## Oracle Configuration

When:

```text
DJ_DB_<ALIAS>_BACKEND=oracle
```

the library supports three Oracle shapes.

### Standard Host / Port / Name

```bash
export DJ_DB_TENANT_BACKEND=oracle
export DJ_DB_TENANT_ORACLE_HOST=oracle.example.com
export DJ_DB_TENANT_ORACLE_PORT=1521
export DJ_DB_TENANT_ORACLE_NAME=ORCLCDB
export DJ_DB_TENANT_ORACLE_USER=scott
export DJ_DB_TENANT_ORACLE_PASSWORD=tiger
```

### Easy Connect

```bash
export DJ_DB_REPORTING_BACKEND=oracle
export DJ_DB_REPORTING_ORACLE_NAME=dbhost.example.com:1521/ORCLPDB1
export DJ_DB_REPORTING_ORACLE_USER=reporter
export DJ_DB_REPORTING_ORACLE_PASSWORD=change-me
```

### Full Descriptor Generation

```bash
export DJ_DB_WAREHOUSE_BACKEND=oracle
export DJ_DB_WAREHOUSE_ORACLE_PROTOCOL=tcp
export DJ_DB_WAREHOUSE_ORACLE_HOST=oracle.example.com
export DJ_DB_WAREHOUSE_ORACLE_PORT=1521
export DJ_DB_WAREHOUSE_ORACLE_SERVICE_NAME=ORCLPDB1
export DJ_DB_WAREHOUSE_ORACLE_USER=warehouse
export DJ_DB_WAREHOUSE_ORACLE_PASSWORD=change-me
```

For Oracle, `OPTIONS["threaded"]` defaults to `True`.

## Supported Built-In Backends

- SQLite
- PostgreSQL
- MySQL
- Oracle
- CockroachDB
- Firebird
- Google Cloud Spanner
- Microsoft SQL Server
- Snowflake
- TiDB
- YugabyteDB
- MongoDB

## Custom Backends

You can register a custom backend:

```python
from dj_db_adapter import register_backend

register_backend(
    "customdb",
    "vendor.backend",
    env_prefix="CUSTOMDB",
    env_map=(("NAME", "NAME"),),
    settings={"NAME"},
)
```

Then configure it like any built-in backend:

```bash
export DJ_DB_CUSTOM_BACKEND=customdb
export DJ_DB_CUSTOM_CUSTOMDB_NAME=mydb
```

## Sample Environment File

A complete example env file for all built-in backends is included in:

`.env.sample`

## Design Notes

This library intentionally avoids implicit database defaults.

- if no DB env vars are set, `databases()` returns `{}`
- if an alias is requested but not configured, `config()` raises
- backend-specific settings are validated instead of silently ignored

That keeps Django database configuration explicit and easier to reason about across environments.
