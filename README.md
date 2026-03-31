# dj-db-adapter

A backend-aware Django database settings adapter inspired by `dj-database-url`.

## Configuration Model

Each database alias is configured through `DJ_DB_<ALIAS>_*`.

Configuration order:

1. `DJ_DB_<ALIAS>_BACKEND`
2. `DJ_DB_<ALIAS>_ENGINE`
3. `DJ_DB_<ALIAS>_URL`
4. `DJ_DB_<ALIAS>_CONFIG_FILE`
5. backend-specific env vars such as `DJ_DB_<ALIAS>_POSTGRES_*`

`BACKEND` chooses the built-in backend and sets Django `ENGINE` automatically.

`ENGINE` is only for explicit override.

## Quick Start

```python
from pathlib import Path

from dj_db_adapter import databases

BASE_DIR = Path(__file__).resolve().parent

DATABASES = databases(base_dir=BASE_DIR)
```

If `DJ_DB_ALIASES` is not set, the adapter uses `default`.

## Public API

`databases(aliases=None, base_dir=None)`

- Returns a Django `DATABASES` mapping.
- If `aliases` is omitted, `DJ_DB_ALIASES` is used.

`config(alias="default", base_dir=None)`

- Returns one database config for the given alias.
- If the alias is `default` and nothing is configured, SQLite is used automatically.

`parse(url)`

- Parses a single database URL.

`register_backend(alias, engine, ...)`

- Registers a custom backend.

## Top-Level Env Vars

These are the primary env vars per alias:

```text
DJ_DB_<ALIAS>_BACKEND=
DJ_DB_<ALIAS>_ENGINE=
DJ_DB_<ALIAS>_URL=
DJ_DB_<ALIAS>_CONFIG_FILE=
```

Examples:

```bash
export DJ_DB_ALIASES=default,analytics
export DJ_DB_DEFAULT_BACKEND=postgres
export DJ_DB_ANALYTICS_URL=mysql://report:secret@mysql.example.com:3306/warehouse
```

## JSON And INI Config Files

Each alias can load config from:

```text
DJ_DB_<ALIAS>_CONFIG_FILE=
```

Supported file formats:

- `.json`
- `.ini`
- `.cfg`

### JSON Example

```json
{
  "BACKEND": "postgres",
  "NAME": "main",
  "USER": "app",
  "PASSWORD": "secret",
  "HOST": "db.example.com",
  "PORT": 5432
}
```

### INI Example

```ini
[database]
backend = postgres
name = archive
user = archiver
password = secret
host = pg.example.com
port = 5432

[options]
application_name = archive-worker
```

INI rules:

- `[database]` maps to top-level database settings
- `[options]` maps to `OPTIONS`
- `[test]` maps to `TEST`

## Multiple Aliases

```bash
export DJ_DB_ALIASES=default,analytics,archive

export DJ_DB_DEFAULT_BACKEND=postgres
export DJ_DB_DEFAULT_POSTGRES_NAME=main
export DJ_DB_DEFAULT_POSTGRES_USER=app
export DJ_DB_DEFAULT_POSTGRES_PASSWORD=secret
export DJ_DB_DEFAULT_POSTGRES_HOST=db.example.com
export DJ_DB_DEFAULT_POSTGRES_PORT=5432

export DJ_DB_ANALYTICS_URL=mysql://report:secret@mysql.example.com:3306/warehouse
export DJ_DB_ARCHIVE_CONFIG_FILE=/etc/myapp/archive.ini
```

## PostgreSQL Env Shape

When `DJ_DB_<ALIAS>_BACKEND=postgres`, use:

```text
DJ_DB_<ALIAS>_POSTGRES_USER=
DJ_DB_<ALIAS>_POSTGRES_NAME=
DJ_DB_<ALIAS>_POSTGRES_HOST=
DJ_DB_<ALIAS>_POSTGRES_PORT=
DJ_DB_<ALIAS>_POSTGRES_PASSWORD=
```

Common Django connection flags for PostgreSQL use the same backend prefix:

```text
DJ_DB_<ALIAS>_POSTGRES_CONN_MAX_AGE=
DJ_DB_<ALIAS>_POSTGRES_CONN_HEALTH_CHECKS=
DJ_DB_<ALIAS>_POSTGRES_AUTOCOMMIT=
DJ_DB_<ALIAS>_POSTGRES_ATOMIC_REQUESTS=
DJ_DB_<ALIAS>_POSTGRES_DISABLE_SERVER_SIDE_CURSORS=
```

Example:

```bash
export DJ_DB_DEFAULT_BACKEND=postgres
export DJ_DB_DEFAULT_POSTGRES_USER=app
export DJ_DB_DEFAULT_POSTGRES_NAME=main
export DJ_DB_DEFAULT_POSTGRES_HOST=db.example.com
export DJ_DB_DEFAULT_POSTGRES_PORT=5432
export DJ_DB_DEFAULT_POSTGRES_PASSWORD=secret
export DJ_DB_DEFAULT_POSTGRES_CONN_MAX_AGE=120
export DJ_DB_DEFAULT_POSTGRES_CONN_HEALTH_CHECKS=true
export DJ_DB_DEFAULT_POSTGRES_AUTOCOMMIT=false
```

## PostgreSQL Options

PostgreSQL `OPTIONS` can be passed only through:

```text
DJ_DB_<ALIAS>_POSTGRES__OPTIONS__<OPTION_NAME>=
```

Examples:

```bash
export DJ_DB_DEFAULT_POSTGRES__OPTIONS__APPLICATION_NAME=api
export DJ_DB_DEFAULT_POSTGRES__OPTIONS__SEARCH_PATH=public,tenant
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

Unsupported PostgreSQL options raise `ValueError`.

## Oracle Variants

When `DJ_DB_<ALIAS>_BACKEND=oracle`, the adapter supports:

1. Standard host / port / name
2. Easy connect through `NAME`
3. Full descriptor generation through `PROTOCOL`, `HOST`, `PORT`, and `SERVICE_NAME`

### Standard

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
export DJ_DB_REPORTING_ORACLE_PASSWORD=secret
```

### Full Descriptor

```bash
export DJ_DB_WAREHOUSE_BACKEND=oracle
export DJ_DB_WAREHOUSE_ORACLE_PROTOCOL=tcp
export DJ_DB_WAREHOUSE_ORACLE_HOST=oracle.example.com
export DJ_DB_WAREHOUSE_ORACLE_PORT=1521
export DJ_DB_WAREHOUSE_ORACLE_SERVICE_NAME=ORCLPDB1
export DJ_DB_WAREHOUSE_ORACLE_USER=warehouse
export DJ_DB_WAREHOUSE_ORACLE_PASSWORD=secret
```

For Oracle, `OPTIONS.threaded` defaults to `True`.

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

Then configure it like:

```bash
export DJ_DB_CUSTOM_BACKEND=customdb
export DJ_DB_CUSTOM_CUSTOMDB_NAME=mydb
```
