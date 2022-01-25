"""
Test User CRUD
"""

import os
import uuid
from http import HTTPStatus

import requests

USERS_TEST_URL = os.environ.get('USERS_TEST_URL', '127.0.0.1:5000')


def test_get(connections):

    user_uuid = connections.uuid['user_id']
    params = {'action_key': 'fake key'}
    response = requests.get(f"http://{USERS_TEST_URL}/user/role/{user_uuid}",
                            params=params)
    assert response.status_code == HTTPStatus.FORBIDDEN

    params = {'action_key': connections.action_keys['user_m']}
    user_uuid = str(uuid.uuid4())
    response = requests.get(f"http://{USERS_TEST_URL}/user/role/{user_uuid}",
                            params=params)
    assert response.status_code == HTTPStatus.NOT_FOUND

    user_uuid = connections.uuid['user_id']
    response = requests.get(f"http://{USERS_TEST_URL}/user/role/{user_uuid}",
                            params=params)
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == 3

    user_uuid = connections.uuid['user_2_id']
    response = requests.get(f"http://{USERS_TEST_URL}/user/role/{user_uuid}",
                            params=params)
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == 0


def test_post(connections):
    data = {'action_key': 'fake_key',
            'role_uuid': str(uuid.uuid4())}
    user_uuid = connections.uuid['user_2_id']

    response = requests.post(f"http://{USERS_TEST_URL}/user/role/{user_uuid}",
                             data=data)
    assert response.status_code == HTTPStatus.FORBIDDEN

    data['action_key'] = connections.action_keys['user_m']
    fake_uuid = str(uuid.uuid4())
    response = requests.post(f"http://{USERS_TEST_URL}/user/role/{fake_uuid}",
                             data=data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = requests.post(f"http://{USERS_TEST_URL}/user/role/{user_uuid}",
                             data=data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    role_uuid = connections.uuid['role_id']
    data['role_uuid'] = role_uuid

    response = requests.post(f"http://{USERS_TEST_URL}/user/role/{user_uuid}",
                             data=data)
    assert response.status_code == HTTPStatus.CREATED

    with connections.pg.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users_auth.users_roles WHERE user_id=%s AND role_id=%s",
                    (user_uuid, role_uuid,))
        assert cur.fetchone()[0] == 1

        cur.execute("DELETE FROM users_auth.users_roles WHERE user_id=%s AND role_id=%s",
                    (user_uuid, role_uuid,))
        assert cur.rowcount == 1
    connections.pg.commit()


def test_delete(connections):
    user_uuid = connections.uuid['user_2_id']
    role_uuid = connections.uuid['role_id']
    data = {'role_uuid': role_uuid,
            'action_key': connections.action_keys['user_m']}
    response = requests.post(f"http://{USERS_TEST_URL}/user/role/{user_uuid}",
                             data=data)
    assert response.status_code == HTTPStatus.CREATED

    data['action_key'] = 'fake_key'
    response = requests.delete(f"http://{USERS_TEST_URL}/user/role/{user_uuid}",
                               data=data)
    assert response.status_code == HTTPStatus.FORBIDDEN

    data['action_key'] = connections.action_keys['user_m']
    user_uuid = str(uuid.uuid4())
    response = requests.delete(f"http://{USERS_TEST_URL}/user/role/{user_uuid}",
                               data=data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    user_uuid = connections.uuid['user_2_id']
    data['role_uuid'] = str(uuid.uuid4())
    response = requests.delete(f"http://{USERS_TEST_URL}/user/role/{user_uuid}",
                               data=data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    data['role_uuid'] = role_uuid
    response = requests.delete(f"http://{USERS_TEST_URL}/user/role/{user_uuid}",
                               data=data)
    assert response.status_code == HTTPStatus.OK

    with connections.pg.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users_auth.users_roles WHERE user_id=%s AND role_id=%s",
                    (user_uuid, role_uuid,))
        assert cur.fetchone()[0] == 0
