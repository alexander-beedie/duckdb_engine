from functools import lru_cache
from typing import Dict, Set, Type, Union

import duckdb
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.engine import Dialect
from sqlalchemy.sql.type_api import TypeEngine

TYPES: Dict[Type, TypeEngine] = {int: Integer(), str: String(), bool: Boolean()}


@lru_cache()
def get_core_config() -> Set[str]:
    # List of connection string parameters that are supported by MotherDuck
    # See: https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/authenticating-to-motherduck/
    motherduck_config_keys = {"motherduck_token", "attach_mode", "saas_mode"}

    rows = (
        duckdb.connect(":memory:")
        .execute("SELECT name FROM duckdb_settings()")
        .fetchall()
    )
    return {name for (name,) in rows} | motherduck_config_keys


def apply_config(
    dialect: Dialect,
    conn: duckdb.DuckDBPyConnection,
    ext: Dict[str, Union[str, int, bool]],
) -> None:
    # TODO: does sqlalchemy have something that could do this for us?
    processors = {k: v.literal_processor(dialect=dialect) for k, v in TYPES.items()}

    for k, v in ext.items():
        process = processors[type(v)]
        assert process, f"Not able to configure {k} with {v}"
        conn.execute(f"SET {k} = {process(v)}")
