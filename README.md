# dj-db-adapter

A backend-aware Django database settings adapter inspired by `dj-database-url`.

It supports:

- Django's officially supported databases: SQLite, PostgreSQL, MySQL and Oracle
- documented third-party backends such as CockroachDB, Firebird, Spanner, SQL Server, Snowflake, TiDB, YugabyteDB and MongoDB
- environment-based configuration through `DATABASE_URL` and `DJANGO_DB_*`
- file-based configuration through the matching `*_FILE` variables

Example:

```python
from pathlib import Path

from dj_db_adapter import config

BASE_DIR = Path(__file__).resolve().parent

DATABASES = {
    "default": config(base_dir=BASE_DIR),
}
```
