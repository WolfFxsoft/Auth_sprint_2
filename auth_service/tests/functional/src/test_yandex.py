
import json
import uuid
import os
from http import HTTPStatus
import pytest
import requests

import auth_lib


TEST_TOKEN = None
AUTH_TEST_URL = os.environ.get('AUTH_TEST_URL', '127.0.0.1:5001')

@pytest.mark.skipif(TEST_TOKEN is None, reason="I need test token")
def test_post_refresh(connections):

    response = requests.post(f'http://{AUTH_TEST_URL}/auth/yandex',
                             data={})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    user_info = auth_lib.yandex.get_user_info(TEST_TOKEN)
    with connections.pg.cursor() as cur:
        user_uuid = str(uuid.uuid4())
        service_id = user_info.get('uid', None)
        assert service_id is not None

        cur.execute("""
        INSERT INTO users_auth.login_pass
        (user_id, login, service, service_id)
        VALUES (%s, 'test_login', 'yandex', %s)""",
                    (user_uuid, service_id))
        assert cur.rowcount == 1
        connections.pg.commit()

        response = requests.post(f'http://{AUTH_TEST_URL}/auth/yandex',
                                 data={'token': TEST_TOKEN,
                                       'user_agent': 'test environment'})
        assert response.status_code == HTTPStatus.ACCEPTED
        response_json = response.json()
        refresh_key = response_json['refresh_key']
        connections.redis_clean.append(refresh_key)

        cur.execute("""
        SELECT * FROM users_auth.users_sessions
        WHERE user_id=%s AND user_agent='test environment';""",
                    (user_uuid,))
        response = list(cur.fetchall())
        assert len(response) == 1
        assert response[0][3] == 'test environment'

        redis_rec = json.loads(connections.redis.get(f"user:{refresh_key}"))
        assert redis_rec['user_id'] == user_uuid



        cur.execute("DELETE FROM users_auth.login_pass WHERE user_id=%s",
                    (user_uuid,))
    connections.pg.commit()

@pytest.mark.skip
@pytest.mark.skipif(TEST_TOKEN is None, reason="I need test token")
def test_yandex_rate_limit(connections):
    # check rate limit
    response_status = []
    for _ in range(4):
        response = requests.post(f'http://{AUTH_TEST_URL}/auth/yandex',
                                 data={'token': TEST_TOKEN,
                                       'user_agent': 'test environment'})
        response_status.append(response.status_code)
    assert HTTPStatus.TOO_MANY_REQUESTS in response_status
