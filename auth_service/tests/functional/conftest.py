import dataclasses
import uuid
from typing import Dict, List, Any

import psycopg2
import pytest
import redis

import pydantic

import auth_lib
import logging


class DBConfig(pydantic.BaseSettings):
    """ get postgresql connection options """
    name: str = pydantic.Field(env='DB_NAME')
    user: str = pydantic.Field(env='DB_USER')
    password: str = pydantic.Field(env='DB_PASSWORD')

    class Config:
        env_file = '.env.test'
        env_file_encoding = 'utf-8'

@dataclasses.dataclass
class Connections():
    pg: psycopg2.extensions.connection
    redis: Any
    redis_clean: List[str]
    uuid: Dict


def cleare_postgres(db_conn):
    cur = db_conn.cursor()
    cur.execute("""DELETE FROM users_auth.users_sessions""")
    cur.execute("""DELETE FROM users_auth.users_roles;""")
    cur.execute("""DELETE FROM users_auth.roles;""")
    cur.execute("""DELETE FROM users_auth.login_pass;""")
    db_conn.commit()
    cur.close()


@pytest.fixture(scope='session')
def connections() -> Connections:
    db_conf = DBConfig()
    pg_conn = psycopg2.connect(host='127.0.0.1',
                               dbname=db_conf.name,
                               user=db_conf.user,
                               password=db_conf.password)

    redis_con = redis.Redis()
    user_id = str(uuid.uuid4())
    login_pass_rec = (user_id,
                      'mylogin',
                      auth_lib.pass_hasher('mypassword'))

    role_id = str(uuid.uuid4())
    role_rec = (role_id,
                'guest',
                'text guest')


    return_connections = Connections(pg=pg_conn,
                                     redis=redis_con,
                                     redis_clean=[],
                                     uuid={'user_id': user_id,
                                           'role_id': role_id})

    cleare_postgres(pg_conn)
    try:
        cur = pg_conn.cursor()
        cur.execute("""INSERT INTO users_auth.login_pass (user_id, login, password) VALUES (%s, %s, %s);""",
                    login_pass_rec)
        assert cur.rowcount == 1
        cur.execute("""INSERT INTO users_auth.roles (role_id, name_short, description) VALUES (%s, %s, %s);""",
                    role_rec)
        assert cur.rowcount == 1
        cur.execute("""INSERT INTO users_auth.users_roles (user_id, role_id) VALUES (%s, %s);""",
                    (user_id, role_id,))
        assert cur.rowcount == 1
        pg_conn.commit()
        cur.close()

        yield return_connections
    except Exception:
        logging.exception('Exception until prepare testing')
    finally:

        redis_con.delete(*return_connections.redis_clean)
        for key in redis_con.scan_iter("deny:*"):
            redis_con.delete(key)
        for key in redis_con.scan_iter("rate:*"):
            redis_con.delete(key)
        cleare_postgres(pg_conn)
        pg_conn.close()
