"""
Test User CRUD
"""

import os
import uuid
from http import HTTPStatus

import requests
from auth_lib import pass_hasher

USERS_TEST_URL = os.environ.get('USERS_TEST_URL', '127.0.0.1:5000')

def test_get_list(connections):
    response = requests.get(f"http://{USERS_TEST_URL}/user/",
                            params={'action_key': 'fake_key'})
    assert response.status_code == HTTPStatus.FORBIDDEN

    response = requests.get(f"http://{USERS_TEST_URL}/user",
                            params={'action_key': connections.action_keys['user_m']})
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == 2


def test_get_user(connections):
    response = requests.get(f"http://{USERS_TEST_URL}/user/{connections.uuid['user_id']}",
                            params={'action_key': 'fake_key'})
    assert response.status_code == HTTPStatus.FORBIDDEN

    fake_uuid = str(uuid.uuid4())
    response = requests.get(f"http://{USERS_TEST_URL}/user/{fake_uuid}",
                            params={'action_key': connections.action_keys['user_m']})
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = requests.get(f"http://{USERS_TEST_URL}/user/{connections.uuid['user_id']}",
                            params={'action_key': connections.action_keys['user_m']})
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['login'] == 'mylogin'
    assert data['first_name'] == 'First Name'


def test_post_user(connections):
    data = {'action_key': 'fake_key',
            'login': 'mylogin',
            'password': 'test',
            'first_name': 'Test First',
            'second_name': 'Test Second'}

    response = requests.post(f"http://{USERS_TEST_URL}/user/",
                             data=data)
    assert response.status_code == HTTPStatus.FORBIDDEN

    data['action_key'] = connections.action_keys['user_m']
    response = requests.post(f"http://{USERS_TEST_URL}/user/",
                             data=data)
    assert response.status_code == HTTPStatus.CONFLICT

    data['login'] = 'test_login'
    response = requests.post(f"http://{USERS_TEST_URL}/user/",
                             data=data)
    assert response.status_code == HTTPStatus.OK
    user_uuid = response.json()['user_uuid']

    with connections.pg.cursor() as cur:
        cur.execute("SELECT user_id, first_name, second_name FROM users_auth.users_data WHERE user_id=%s",
                    (user_uuid,))
        rec = list(cur.fetchone())
        rec[1] = rec[1].strip()
        rec[2] = rec[2].strip()

        assert rec == [user_uuid,
                       'Test First',
                       'Test Second']
        cur.execute("DELETE FROM users_auth.users_data WHERE user_id=%s",
                    (user_uuid,))
        assert cur.rowcount == 1

        cur.execute("SELECT user_id, login, password FROM users_auth.login_pass WHERE user_id=%s",
                    (user_uuid,))
        rec = list(cur.fetchone())
        rec[1] = rec[1].strip()

        assert rec == [user_uuid,
                       'test_login',
                       pass_hasher('test')]
        cur.execute("DELETE FROM users_auth.login_pass WHERE user_id=%s",
                    (user_uuid,))
        assert cur.rowcount == 1
    connections.pg.commit()


def test_delete_user(connections):
    data = {'action_key': connections.action_keys['user_m'],
            'login': 'test_login',
            'password': 'test',
            'first_name': 'Test First',
            'second_name': 'Test Second'}

    response = requests.post(f"http://{USERS_TEST_URL}/user/",
                             data=data)
    assert response.status_code == HTTPStatus.OK
    user_uuid = response.json()['user_uuid']

    data = {'action_key': 'fake key'}
    response = requests.delete(f"http://{USERS_TEST_URL}/user/{user_uuid}",
                               data=data)
    assert response.status_code == HTTPStatus.FORBIDDEN

    data = {'action_key': connections.action_keys['user_m']}
    response = requests.delete(f"http://{USERS_TEST_URL}/user/{user_uuid}",
                               data=data)
    assert response.status_code == HTTPStatus.OK

    with connections.pg.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users_auth.login_pass WHERE user_id=%s",
                    (user_uuid,))
        assert cur.fetchone()[0] == 0

        cur.execute("SELECT COUNT(*) FROM users_auth.users_data WHERE user_id=%s",
                    (user_uuid,))
        assert cur.fetchone()[0] == 0


def test_put(connections):
    data = {'action_key': connections.action_keys['user_m'],
            'login': 'test_put',
            'password': 'test',
            'first_name': 'Test First',
            'second_name': 'Test Second'}

    response = requests.post(f"http://{USERS_TEST_URL}/user/",
                             data=data)
    assert response.status_code == HTTPStatus.OK
    user_uuid = response.json()['user_uuid']

    data = {'action_key': 'fake_key',
            'first_name': 'New First',
            'second_name': 'New Second'}
    response = requests.put(f"http://{USERS_TEST_URL}/user/{user_uuid}",
                            data=data)
    assert response.status_code == HTTPStatus.FORBIDDEN

    data['action_key'] = connections.action_keys['user_m']
    fake_user_uuid = str(uuid.uuid4())
    response = requests.put(f"http://{USERS_TEST_URL}/user/{fake_user_uuid}",
                            data=data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = requests.put(f"http://{USERS_TEST_URL}/user/{user_uuid}",
                            data=data)
    assert response.status_code == HTTPStatus.OK

    with connections.pg.cursor() as cur:
        cur.execute("SELECT first_name, second_name FROM users_auth.users_data WHERE user_id=%s",
                    (user_uuid,))
        rec = list(cur.fetchone())
        assert rec[0].strip() == 'New First'
        assert rec[1].strip() == 'New Second'

    data = {'action_key': connections.action_keys['user_m']}
    response = requests.delete(f"http://{USERS_TEST_URL}/user/{user_uuid}",
                               data=data)
    assert response.status_code == HTTPStatus.OK


def test_put_password(connections):
    data = {'action_key': connections.action_keys['user_m'],
            'login': 'test_put',
            'password': 'test',
            'first_name': 'Test First',
            'second_name': 'Test Second'}

    response = requests.post(f"http://{USERS_TEST_URL}/user/",
                             data=data)
    assert response.status_code == HTTPStatus.OK
    user_uuid = response.json()['user_uuid']

    data = {'action_key': 'fake_key',
            'password': 'new_pass',}
    response = requests.put(f"http://{USERS_TEST_URL}/user/password/{user_uuid}",
                            data=data)
    assert response.status_code == HTTPStatus.FORBIDDEN

    data['action_key'] = connections.action_keys['user_m']
    fake_user_uuid = str(uuid.uuid4())
    response = requests.put(f"http://{USERS_TEST_URL}/user/password/{fake_user_uuid}",
                            data=data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = requests.put(f"http://{USERS_TEST_URL}/user/password/{user_uuid}",
                            data=data)
    assert response.status_code == HTTPStatus.OK

    with connections.pg.cursor() as cur:
        cur.execute("SELECT password FROM users_auth.login_pass WHERE user_id=%s",
                    (user_uuid,))
        rec = list(cur.fetchone())
        assert rec[0].strip() == pass_hasher('new_pass')


    data = {'action_key': connections.action_keys['user_m']}
    response = requests.delete(f"http://{USERS_TEST_URL}/user/{user_uuid}",
                               data=data)
    assert response.status_code == HTTPStatus.OK
