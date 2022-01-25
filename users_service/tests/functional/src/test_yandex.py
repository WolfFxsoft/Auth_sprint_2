"""
Test Yandex functions
"""
import os
from http import HTTPStatus

import pytest
import requests

from auth_lib import pass_hasher

USERS_TEST_URL = os.environ.get('USERS_TEST_URL', '127.0.0.1:5000')
TEST_TOKEN = None


@pytest.mark.skipif(TEST_TOKEN is None, reason="I need test token")
def test_post_create_user(connections):

    data = {'action_key': 'fake_key',
            'token': TEST_TOKEN}
    response = requests.post(f"http://{USERS_TEST_URL}/user/yandex",
                             data=data)
    assert response.status_code == HTTPStatus.FORBIDDEN

    data = {'action_key': connections.action_keys['user_m'],
            'token': 'fake_token'}
    response = requests.post(f"http://{USERS_TEST_URL}/user/yandex",
                             data=data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    data['token'] = TEST_TOKEN
    response = requests.post(f"http://{USERS_TEST_URL}/user/yandex",
                             data=data)
    assert response.status_code == HTTPStatus.CREATED
    user_uuid = response.json().get('user_uuid', None)
    assert user_uuid

    with connections.pg.cursor() as cur:
        cur.execute("SELECT login, password, service, service_id FROM users_auth.login_pass WHERE user_id=%s",
                    (user_uuid,))
        login_pass_rec = list(cur.fetchone())
        assert login_pass_rec[0]
        assert login_pass_rec[1] is None
        assert login_pass_rec[2] == 'yandex'
        assert login_pass_rec[3]

        cur.execute("SELECT first_name, second_name FROM users_auth.users_data WHERE user_id=%s",
                    (user_uuid,))
        users_data_rec = list(cur.fetchone())
        assert users_data_rec[0]
        assert users_data_rec[1]

        cur.execute("DELETE FROM users_auth.login_pass WHERE user_id=%s",
                    (user_uuid,))
        cur.execute("DELETE FROM users_auth.users_data WHERE user_id=%s",
                    (user_uuid,))
    connections.pg.commit()


@pytest.mark.skipif(TEST_TOKEN is None, reason="I need test token")
def test_post_recoonect_user(connections):
    data = {'action_key': connections.action_keys['user_m'],
            'token': TEST_TOKEN}
    response = requests.post(f"http://{USERS_TEST_URL}/user/yandex",
                             data=data)
    assert response.status_code == HTTPStatus.CREATED
    user_uuid = response.json().get('user_uuid', None)
    assert user_uuid

    data = {'action_key': 'fake_key'}
    response = requests.delete(f"http://{USERS_TEST_URL}/user/yandex/{user_uuid}",
                               data=data)
    assert response.status_code == HTTPStatus.FORBIDDEN

    data = {'action_key': connections.action_keys['user_m'],}
    response = requests.delete(f"http://{USERS_TEST_URL}/user/yandex/{user_uuid}",
                               data=data)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    data = {'action_key': connections.action_keys['user_m'],
            'password': 'test_pass'}
    response = requests.delete(f"http://{USERS_TEST_URL}/user/yandex/{user_uuid}",
                               data=data)
    assert response.status_code == HTTPStatus.OK


    with connections.pg.cursor() as cur:
        cur.execute("SELECT login, password, service, service_id FROM users_auth.login_pass WHERE user_id=%s",
                    (user_uuid,))
        login_pass_rec = list(cur.fetchone())
        assert login_pass_rec[0]
        assert login_pass_rec[1] == pass_hasher('test_pass')
        assert login_pass_rec[2] == 'self'
        assert login_pass_rec[3] is None

        cur.execute("DELETE FROM users_auth.login_pass WHERE user_id=%s",
                    (user_uuid,))
        cur.execute("DELETE FROM users_auth.users_data WHERE user_id=%s",
                    (user_uuid,))
    connections.pg.commit()
