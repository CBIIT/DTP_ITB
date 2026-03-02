"""
oracle_connection.py — Shared Oracle database connection helper.

All bridge scripts import ``get_connection()`` from here so that
credential handling and Oracle Instant Client initialisation live in
one place.
"""

import os

# Environment variable names used for Oracle credentials.
_ENV_USER = "ORACLE_USER"
_ENV_PASSWORD = "ORACLE_PASSWORD"
_ENV_DSN = "ORACLE_CONNECTION_STRING"
_ENV_CLIENT = "ORACLE_CLIENT_PATH"


def _clean_env(key: str) -> str:
    """Return the value of *key* from the environment.

    A common misconfiguration in ``.env.local`` is accidentally
    duplicating the variable name inside the value, e.g.::

        ORACLE_CONNECTION_STRING=ORACLE_CONNECTION_STRING=host:port/service

    This helper strips the ``KEY=`` prefix when present so the
    downstream Oracle driver receives only the actual value.

    Raises a clear error when the variable is not set.
    """
    value = os.environ.get(key)
    if value is None:
        raise RuntimeError(
            f"Environment variable {key} is not set. "
            "Please configure it in .env.local."
        )
    prefix = f"{key}="
    if value.startswith(prefix):
        value = value[len(prefix):]
    return value


def get_connection():
    """Create and return an Oracle database connection."""
    import oracledb

    user = _clean_env(_ENV_USER)
    password = _clean_env(_ENV_PASSWORD)
    dsn = _clean_env(_ENV_DSN)

    # Use thick mode when Oracle Instant Client is available
    client_path = os.environ.get(_ENV_CLIENT)
    if client_path:
        oracledb.init_oracle_client(lib_dir=client_path)

    return oracledb.connect(user=user, password=password, dsn=dsn)
