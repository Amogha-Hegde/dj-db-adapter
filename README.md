# dj-db-adapter

A backend-aware Django database settings adapter inspired by `dj-database-url`.

It supports:

- one module per backend instead of a shared official/unofficial split
- multiple aliases at the same time through `databases()`
- alias-specific URLs such as `DJANGO_DATABASE_DEFAULT_URL` and `DJANGO_DATABASE_ANALYTICS_URL`
- per-alias JSON, YAML, and INI config files through `DJANGO_DATABASE_<ALIAS>_CONFIG` or `DJANGO_DATABASE_<ALIAS>_CONFIG_FILE`
- strict backend-specific settings validation so unsupported keys fail fast

## Installation

```bash
pip install dj-db-adapter
```

If you want YAML-based config files, `PyYAML` is already included as a package dependency.

## Quick Start

Use `databases()` when you want a full Django `DATABASES` mapping:

```python
from pathlib import Path

from dj_db_adapter import databases

BASE_DIR = Path(__file__).resolve().parent

DATABASES = databases(base_dir=BASE_DIR)
```

Use `config(alias)` when you want one alias only:

```python
from dj_db_adapter import config

DATABASES = {
    "default": config("default"),
    "analytics": config("analytics"),
}
```

## Public API

`databases(aliases=None, base_dir=None)`

- Returns a Django `DATABASES` dict for all aliases.
- If `aliases` is omitted, `DJANGO_DATABASE_ALIASES` is used.
- If no alias list is provided, it defaults to `default`.

`config(alias="default", base_dir=None)`

- Returns the config for a single alias.
- For the `default` alias, SQLite is used automatically when no engine or URL is provided.

`parse(url)`

- Parses a single database URL into a Django database config.

`register_backend(alias, engine, ...)`

- Registers a custom backend alias and its allowed settings/env mappings.

## Alias Naming

Alias-specific env vars use this format:

```text
DJANGO_DATABASE_<ALIAS>_<SETTING>
```

Examples:

- `DJANGO_DATABASE_DEFAULT_URL`
- `DJANGO_DATABASE_ANALYTICS_URL`
- `DJANGO_DATABASE_REPORTING_ENGINE`
- `DJANGO_DATABASE_TENANT_A_CONFIG`

Alias names are uppercased and `-` is converted to `_`.

If the alias is `default`, these fallbacks are also accepted:

- `DJANGO_DATABASE_URL`
- `DATABASE_URL`
- `DJANGO_DATABASE_ENGINE`
- `DJANGO_DATABASE_NAME`
- and the matching `*_FILE` variants

## Multiple Databases

Example:

```bash
export DJANGO_DATABASE_ALIASES=default,analytics,archive
export DJANGO_DATABASE_DEFAULT_URL=postgres://app:secret@db.example.com:5432/main
export DJANGO_DATABASE_ANALYTICS_URL=mysql://report:secret@mysql.example.com:3306/warehouse
export DJANGO_DATABASE_ARCHIVE_ENGINE=sqlite
export DJANGO_DATABASE_ARCHIVE_NAME=/srv/archive.sqlite3
```

```python
from dj_db_adapter import databases

DATABASES = databases()
```

## Configuration Sources

Each alias can be configured from:

1. direct env vars
2. `*_FILE` env vars
3. per-alias config files in JSON, YAML, or INI
4. database URLs

Env values override file config values for the same alias.

## Value From File

Any normal setting can also be provided through a matching `*_FILE` variable.

Example:

```bash
export DJANGO_DATABASE_DEFAULT_URL_FILE=/run/secrets/default_database_url
export DJANGO_DATABASE_ANALYTICS_PASSWORD_FILE=/run/secrets/analytics_db_password
```

The adapter reads the file contents and uses that value.

## Per-Alias Config Files

Each alias can point to a config file using:

- `DJANGO_DATABASE_<ALIAS>_CONFIG`
- `DJANGO_DATABASE_<ALIAS>_CONFIG_FILE`

`CONFIG` is treated as a file path, not as inline file content.

Supported file formats:

- `.json`
- `.yaml`
- `.yml`
- `.ini`
- `.cfg`

### JSON Example

```json
{
  "ENGINE": "postgres",
  "NAME": "main",
  "HOST": "db.example.com",
  "PORT": 5432,
  "USER": "app",
  "PASSWORD": "secret",
  "OPTIONS": {
    "sslmode": "require"
  }
}
```

### YAML Example

```yaml
engine: mongodb
name: analytics
host: mongodb://mongo.example.com:27017/analytics
```

### INI Example

```ini
[database]
engine = postgres
name = archive
host = pg.example.com
port = 5432
user = archiver
password = secret

[options]
sslmode = require

[test]
name = archive_test
```

INI rules:

- `[database]` maps to top-level Django DB settings
- `[options]` maps to `OPTIONS`
- `[test]` maps to `TEST`

## Supported Backends

Built-in backend modules currently cover:

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

## Backend-Specific Settings

Each backend only accepts its own supported settings plus common Django connection settings such as:

- `ENGINE`
- `OPTIONS`
- `TEST`
- `CONN_MAX_AGE`
- `CONN_HEALTH_CHECKS`
- `ATOMIC_REQUESTS`
- `AUTOCOMMIT`
- `DISABLE_SERVER_SIDE_CURSORS`

If you pass unsupported keys for a backend, the adapter raises `ValueError`.

## URL-Based Configuration

Examples:

```bash
export DJANGO_DATABASE_DEFAULT_URL=postgres://user:pass@db.example.com:5432/app?sslmode=require
export DJANGO_DATABASE_ANALYTICS_URL=mysql://user:pass@mysql.example.com:3306/warehouse
export DJANGO_DATABASE_MONGO_URL=mongodb://mongo.example.com:27017/analytics
```

The parser maps aliases like `postgres`, `mysql`, `oracle`, `sqlite`, `snowflake`, `mongodb`, and others to their Django backend engine strings.

## Oracle Configuration Variants

Oracle supports three common shapes.

### 1. Standard Host / Port / Name

```bash
export DJANGO_DATABASE_TENANT_ENGINE=oracle
export DJANGO_DATABASE_TENANT_HOST=oracle.example.com
export DJANGO_DATABASE_TENANT_PORT=1521
export DJANGO_DATABASE_TENANT_NAME=ORCLCDB
export DJANGO_DATABASE_TENANT_USER=scott
export DJANGO_DATABASE_TENANT_PASSWORD=tiger
```

### 2. Easy Connect

```bash
export DJANGO_DATABASE_REPORTING_ENGINE=oracle
export DJANGO_DATABASE_REPORTING_NAME=dbhost.example.com:1521/ORCLPDB1
export DJANGO_DATABASE_REPORTING_USER=reporter
export DJANGO_DATABASE_REPORTING_PASSWORD=secret
```

### 3. Full Descriptor / Service Name

```bash
export DJANGO_DATABASE_WAREHOUSE_ENGINE=oracle
export DJANGO_DATABASE_WAREHOUSE_PROTOCOL=tcp
export DJANGO_DATABASE_WAREHOUSE_HOST=oracle.example.com
export DJANGO_DATABASE_WAREHOUSE_PORT=1521
export DJANGO_DATABASE_WAREHOUSE_SERVICE_NAME=ORCLPDB1
export DJANGO_DATABASE_WAREHOUSE_USER=warehouse
export DJANGO_DATABASE_WAREHOUSE_PASSWORD=secret
```

For Oracle:

- `OPTIONS.threaded` defaults to `True`
- if `SERVICE_NAME` is provided, the adapter builds the Oracle descriptor string into `NAME`

## Common Patterns

### SQLite Default

```python
DATABASES = databases(base_dir=BASE_DIR)
```

If nothing is configured for `default`, this becomes:

```python
{
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

### File Config With Env Override

```bash
export DJANGO_DATABASE_ANALYTICS_CONFIG=/etc/myapp/analytics.json
export DJANGO_DATABASE_ANALYTICS_HOST=override.example.com
```

The file is loaded first, then env values override matching keys.

## Custom Backends

You can register a custom backend:

```python
from dj_db_adapter import register_backend

register_backend(
    "customdb",
    "vendor.backend",
    env_map=(("NAME", "NAME"), ("HOST", "HOST")),
    settings={"NAME", "HOST"},
)
```

Then configure it like any other alias:

```bash
export DJANGO_DATABASE_CUSTOM_ENGINE=customdb
export DJANGO_DATABASE_CUSTOM_NAME=mydb
export DJANGO_DATABASE_CUSTOM_HOST=db.internal
```
