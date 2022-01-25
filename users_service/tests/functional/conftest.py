import dataclasses
import uuid
from http import HTTPStatus
from typing import (Dict, List, Any, Optional)

import psycopg2
import pytest
import redis
import requests

import pydantic
import auth_lib

class Config(pydantic.BaseSettings):
    """ get postgresql connection options """
    name: str = pydantic.Field(env='DB_NAME')
    user: str = pydantic.Field(env='DB_USER')
    password: str = pydantic.Field(env='DB_PASSWORD')

    auth_host: str = pydantic.Field(env='AUTH_HOST')
    auth_port: int = pydantic.Field(env='AUTH_PORT')

    class Config:
        env_file = '.env.test'
        env_file_encoding = 'utf-8'


@dataclasses.dataclass
class Connections():
    pg: psycopg2.extensions.connection
    redis: Any
    redis_clean: List[str]
    uuid: Dict
    action_keys: Optional[Dict]


def cleare_postgres(db_conn):
    cur = db_conn.cursor()
    cur.execute("""DELETE FROM users_auth.users_data""")
    cur.execute("""DELETE FROM users_auth.users_sessions""")
    cur.execute("""DELETE FROM users_auth.users_roles;""")
    cur.execute("""DELETE FROM users_auth.roles;""")
    cur.execute("""DELETE FROM users_auth.login_pass;""")
    db_conn.commit()
    cur.close()


@pytest.fixture(scope='session')
def connections() -> Connections:
    config = Config()
    pg_conn = psycopg2.connect(host='127.0.0.1',
                               dbname=config.name,
                               user=config.user,
                               password=config.password)

    redis_con = redis.Redis()
    user_id = str(uuid.uuid4())
    users_recs = [(user_id, 'mylogin', auth_lib.pass_hasher('mypassword')),
                  (str(uuid.uuid4()), 'user_2', auth_lib.pass_hasher('password')),]

    user_data_recs = [(user_id, "First Name", "Second Name"),]

    role_recs = [(str(uuid.uuid4()), 'guest', 'text guest'),
                 (str(uuid.uuid4()), 'role_m', "roles manager"),
                 (str(uuid.uuid4()), 'user_m', "users manager"),]

    user_roles_rec = [(user_id, x[0]) for x in role_recs]

    return_connections = Connections(pg=pg_conn,
                                     redis=redis_con,
                                     redis_clean=[],
                                     uuid={'user_id': user_id,
                                           'role_id': role_recs[1][0],
                                           'user_2_id': users_recs[1][0]},
                                     action_keys={})

    cleare_postgres(pg_conn)
    cur = pg_conn.cursor()
    # user append
    cur.executemany("""INSERT INTO users_auth.login_pass (user_id, login, password) VALUES (%s, %s, %s);""",
                    users_recs)
    assert cur.rowcount == 2

    cur.executemany("""INSERT INTO users_auth.users_data (user_id, first_name, second_name) VALUES (%s, %s, %s)""",
                    user_data_recs)
    assert cur.rowcount == 1

    # roles append
    cur.executemany("""INSERT INTO users_auth.roles (role_id, name_short, description) VALUES (%s, %s, %s);""",
                    role_recs)
    assert cur.rowcount == 3

    cur.executemany("""INSERT INTO users_auth.users_roles (user_id, role_id) VALUES (%s, %s);""",
                user_roles_rec)
    assert cur.rowcount == 3

    pg_conn.commit()
    cur.close()

    auth_url = f"http://{config.auth_host}:{config.auth_port}"

    response = requests.post(f'{auth_url}/auth/login',
                             data={'login': 'mylogin',
                                   'password': 'mypassword'})
    assert response.status_code == HTTPStatus.ACCEPTED
    response_json = response.json()
    refresh_key = response_json['refresh_key']
    return_connections.redis_clean.append(refresh_key)

    response = requests.post(f'{auth_url}/auth/refresh',
                             data={'refresh_key': refresh_key,
                                   'role': 'role_m'})
    assert response.status_code == HTTPStatus.ACCEPTED
    response_json = response.json()
    role_m_action_key = response_json['action_key']

    response = requests.post(f'{auth_url}/auth/refresh',
                             data={'refresh_key': refresh_key,
                                    'role': 'user_m'})
    assert response.status_code == HTTPStatus.ACCEPTED
    response_json = response.json()
    user_m_action_key = response_json['action_key']


    return_connections.action_keys = {'role_m': role_m_action_key,
                                      'user_m': user_m_action_key,}

    yield return_connections

    if return_connections.redis_clean:
        redis_con.delete(*return_connections.redis_clean)
    for key in redis_con.scan_iter("deny:*"):
        redis_con.delete(key)
    cleare_postgres(pg_conn)
    pg_conn.close()
