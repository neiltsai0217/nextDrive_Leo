import json
import time
from copy import deepcopy

import psycopg2
from psycopg2 import extras
from addict import Dict

from libs.config_utils import get_config
from libs.log_utils import get_logger

_logger = get_logger(__name__)


def postgres_query_all(sql, **kwargs):
    """dbname: 這個 Postgres 底下要查哪個 database (預設用 variables 設定的
    default_dbname); host/帳密/port 都共用同一組, 不用整組重複設定."""
    def query_all_fn(cursor):
        return cursor.fetchall()

    return _execute('postgres', query_all_fn, sql, **kwargs)


def postgres_query_one(sql, **kwargs):
    """dbname: 這個 Postgres 底下要查哪個 database (預設用 variables 設定的
    default_dbname); host/帳密/port 都共用同一組, 不用整組重複設定."""
    def query_one_fn(cursor):
        return cursor.fetchone()

    return _execute('postgres', query_one_fn, sql, **kwargs)


def postgres_execute(sql, **kwargs):
    """會變更資料的 SQL 入口。

    注意: 依 aquarius-sdet 規範, AI Agent 不得使用本函式執行非 SELECT 語句,
    需要寫入資料時一律交由使用者自行執行。
    """
    def execute_fn(cursor):
        return cursor.rowcount

    return _execute('postgres', execute_fn, sql, **kwargs)


def _pg_connect(database, dbname):
    return psycopg2.connect(
        host=database.host,
        user=database.username,
        password=database.password,
        dbname=dbname or database.default_dbname,
        port=database.port,
        connect_timeout=15,
    )


def _execute(service_name, fn, sql, **kwargs):
    config = get_config()
    role = kwargs.pop('role', None)
    if role:
        user = getattr(config.users, role)
        kwargs['user_id'] = user.user_id

        cell_phone = user.get('cell_phone', None)
        if cell_phone:
            kwargs['cell_phone'] = cell_phone

        email = user.get('email', None)
        if email:
            kwargs['email'] = email

    json_columns = kwargs.pop('json_columns', [])
    dbname = kwargs.pop('dbname', None)
    database = getattr(config.databases, service_name)
    conn = None

    def convert_json_columns(record):
        cloned_record = deepcopy(record)

        for json_column in json_columns:
            json_str = cloned_record.get(json_column)
            if json_str:
                cloned_record[json_column] = json.loads(json_str)

        return cloned_record

    def execute_on_conn(conn):
        conn.autocommit = True
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
            raw_sql = cursor.mogrify(sql, kwargs).decode('utf-8')

            _logger.debug(f"Execute SQL: {raw_sql}.")

            start_time = time.perf_counter()

            cursor.execute(sql, kwargs)
            result = fn(cursor)

            spent_time = int((time.perf_counter() - start_time) * 1000)
            _logger.debug(f"receive result {result} {{executed in {spent_time} msecs}}.")

            if result:
                if isinstance(result, dict):
                    return Dict(convert_json_columns(result))
                elif isinstance(result, list):
                    return [Dict(convert_json_columns(element)) for element in result]
            return result

    try:
        conn = _pg_connect(database, dbname)
        return execute_on_conn(conn)

    except Exception:
        _logger.warning(f"SQL connect failed and retry connect again => [{sql}]")
        conn = _pg_connect(database, dbname)
        return execute_on_conn(conn)

    finally:
        if conn is not None:
            conn.close()
