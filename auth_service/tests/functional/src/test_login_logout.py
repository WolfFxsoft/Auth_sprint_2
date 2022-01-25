"""
Tests
"""
import os
import json
from http import HTTPStatus

import requests

AUTH_TEST_URL = os.environ.get('AUTH_TEST_URL', '127.0.0.1:5001')


def test_login(connections):
    with connections.pg.cursor() as cur:
        response = requests.post(f'http://{AUTH_TEST_URL}/auth/login',
                                 data={'login': 'fakelogin',
                                       'password': 'mypassword'})
        assert response.status_code == HTTPStatus.UNAUTHORIZED

        response = requests.post(f'http://{AUTH_TEST_URL}/auth/login',
                                 data={'login': 'mylogin',
                                       'password': 'mypassword',
                                       'user_agent': 'test environment'})
        assert response.status_code == HTTPStatus.ACCEPTED
        response_json = response.json()
        refresh_key = response_json['refresh_key']
        connections.redis_clean.append(refresh_key)

        cur.execute("""
        SELECT * FROM users_auth.users_sessions
        WHERE user_id=%s AND user_agent='test environment';""",
                    (connections.uuid['user_id'],))
        response = list(cur.fetchall())
        assert len(response) == 1
        assert response[0][3] == 'test environment'

        redis_rec = json.loads(connections.redis.get(f"user:{refresh_key}"))
        assert redis_rec['user_id'] == connections.uuid['user_id']


def test_logout(connections):

    response = requests.post(f'http://{AUTH_TEST_URL}/auth/login',
                             data={'login': 'mylogin',
                                   'password': 'mypassword'})
    assert response.status_code == HTTPStatus.ACCEPTED
    response_json = response.json()
    refresh_key = response_json['refresh_key']
    connections.redis_clean.append(refresh_key)

    response = requests.post(f'http://{AUTH_TEST_URL}/auth/refresh',
                             data={'refresh_key': refresh_key,
                                   'role': 'guest'})
    assert response.status_code == HTTPStatus.ACCEPTED
    response_json = response.json()
    action_key = response_json['action_key']

    response = requests.post(f'http://{AUTH_TEST_URL}/auth/logout',
                             data={'refresh_key': refresh_key,
                                   'role': 'guest'})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    response = requests.post(f'http://{AUTH_TEST_URL}/auth/logout',
                             data={'role': 'guest',
                                   'action_key': action_key})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    response = requests.post(f'http://{AUTH_TEST_URL}/auth/logout',
                             data={'refresh_key': refresh_key,
                                   'action_key': action_key})

    assert response.status_code == HTTPStatus.OK

    redis_rec = connections.redis.get(f"user:{refresh_key}")
    assert redis_rec is None

    redis_rec = connections.redis.get(f"deny:{action_key}")
    assert redis_rec is not None
    assert redis_rec.decode('utf-8') == action_key
