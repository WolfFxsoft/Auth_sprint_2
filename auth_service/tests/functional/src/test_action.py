"""
Test's
"""
import os
from http import HTTPStatus

import requests

AUTH_TEST_URL = os.environ.get('AUTH_TEST_URL', '127.0.0.1:5001')


def test_action(connections):

    with connections.pg.cursor() as cur:
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

        response = requests.post(f'http://{AUTH_TEST_URL}/auth/action',
                                 data={'refresh_key': refresh_key,
                                       'role': 'guest'})
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

        response = requests.post(f'http://{AUTH_TEST_URL}/auth/action',
                                 data={'action_key': 'fake.action.key'})
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = requests.post(f'http://{AUTH_TEST_URL}/auth/action',
                                 data={'action_key': action_key})
        assert response.status_code == HTTPStatus.ACCEPTED


def test_deny_action_key(connections):
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

    # check action_key work well
    response = requests.post(f'http://{AUTH_TEST_URL}/auth/action',
                             data={'action_key': action_key})
    assert response.status_code == HTTPStatus.ACCEPTED
    response_json = response.json()
    action_key = response_json['action_key']



    # check action_key deny after logout
    response = requests.post(f'http://{AUTH_TEST_URL}/auth/logout',
                             data={'refresh_key': refresh_key,
                                   'action_key': action_key})
    assert response.status_code == HTTPStatus.OK

    response = requests.post(f'http://{AUTH_TEST_URL}/auth/action',
                             data={'action_key': action_key})
    assert response.status_code == HTTPStatus.FORBIDDEN
