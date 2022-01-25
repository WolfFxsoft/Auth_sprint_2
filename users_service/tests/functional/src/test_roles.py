"""
Tests
"""
import os
import uuid
from http import HTTPStatus

import requests

USERS_TEST_URL = os.environ.get('USERS_TEST_URL', '127.0.0.1:5000')

def test_get_list(connections):
    response = requests.get(f"http://{USERS_TEST_URL}/role/",
                            params={'action_key': 'fake_key'})
    assert response.status_code == HTTPStatus.FORBIDDEN

    response = requests.get(f"http://{USERS_TEST_URL}/role",
                            params={'action_key': connections.action_keys['role_m']})
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == 3


def test_get_rec(connections):
    response = requests.get(f"http://{USERS_TEST_URL}/role/{connections.uuid['role_id']}",
                            params={'action_key': 'fake_key'})
    assert response.status_code == HTTPStatus.FORBIDDEN

    fake_uuid = str(uuid.uuid4())
    response = requests.get(f"http://{USERS_TEST_URL}/role/{fake_uuid}",
                            params={'action_key': connections.action_keys['role_m']})
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = requests.get(f"http://{USERS_TEST_URL}/role/{connections.uuid['role_id']}",
                            params={'action_key': connections.action_keys['role_m']})
    assert response.status_code == HTTPStatus.OK
    assert response.json()['name_short'] == 'role_m'

    fake_uuid = str(uuid.uuid4())
    response = requests.get(f"http://{USERS_TEST_URL}/role/{fake_uuid}",
                            params={'action_key': connections.action_keys['role_m']})



def test_post(connections):
    response = requests.post(f"http://{USERS_TEST_URL}/role/",
                             data={'action_key': 'fake_key',
                                   'name_short': 'test_role',
                                   'description': 'test role'})
    assert response.status_code == HTTPStatus.FORBIDDEN

    response = requests.post(f"http://{USERS_TEST_URL}/role/",
                             data={'action_key': connections.action_keys['role_m'],
                                   'name_short': 'role_m',
                                   'description': 'test role'})
    assert response.status_code == HTTPStatus.CONFLICT

    response = requests.post(f"http://{USERS_TEST_URL}/role/",
                             data={'action_key': connections.action_keys['role_m'],
                                   'name_short': 'test_role',
                                   'description': 'test role'})
    assert response.status_code == HTTPStatus.CREATED
    role_uuid = response.json()['role_uuid']

    with connections.pg.cursor() as cur:
        cur.execute("""SELECT role_id, name_short, description FROM users_auth.roles WHERE role_id=%s""",
                    (role_uuid,))
        rec = list(cur.fetchone())
        rec[1] = rec[1].strip()
        assert rec == [role_uuid,
                       'test_role',
                       'test role']
        cur.execute("""DELETE FROM users_auth.roles WHERE role_id=%s""",
                    (role_uuid,))
        assert cur.rowcount == 1
    connections.pg.commit()


def test_delete(connections):
    response = requests.post(f"http://{USERS_TEST_URL}/role/",
                             data={'action_key': connections.action_keys['role_m'],
                                   'name_short': 'test_role',
                                   'description': 'test role'})
    assert response.status_code == HTTPStatus.CREATED
    role_uuid = response.json()['role_uuid']

    response = requests.delete(f"http://{USERS_TEST_URL}/role/{role_uuid}",
                               params={'action_key': 'fake_key'})
    assert response.status_code == HTTPStatus.FORBIDDEN

    response = requests.delete(f"http://{USERS_TEST_URL}/role/{role_uuid}",
                               params={'action_key': connections.action_keys['role_m']})
    assert response.status_code == HTTPStatus.OK

    with connections.pg.cursor() as cur:
        cur.execute("""SELECT COUNT(*) FROM users_auth.roles WHERE role_id=%s""",
                    (role_uuid,))
        rec = cur.fetchone()
        assert rec[0] == 0
