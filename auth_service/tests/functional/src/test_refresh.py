"""
Tests
"""
import os
from http import HTTPStatus

import requests


AUTH_TEST_URL = os.environ.get('AUTH_TEST_URL', '127.0.0.1:5001')


def test_refresh(connections):

    response = requests.post(f'http://{AUTH_TEST_URL}/auth/login',
                             data={'login': 'mylogin',
                                   'password': 'mypassword'})
    assert response.status_code == HTTPStatus.ACCEPTED
    response_json = response.json()
    refresh_key = response_json['refresh_key']
    connections.redis_clean.append(refresh_key)

    response = requests.post(f'http://{AUTH_TEST_URL}/auth/refresh',
                             data={'login': 'mylogin',
                                   'password': 'mypassword'})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    response = requests.post(f'http://{AUTH_TEST_URL}/auth/refresh',
                             data={'refresh_key': 'fake_key',
                                   'role': 'fake'})
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = requests.post(f'http://{AUTH_TEST_URL}/auth/refresh',
                             data={'refresh_key': refresh_key,
                                   'role': 'fake'})
    assert response.status_code == HTTPStatus.FORBIDDEN

    response = requests.post(f'http://{AUTH_TEST_URL}/auth/refresh',
                             data={'refresh_key': refresh_key,
                                   'role': 'guest'})
    assert response.status_code == HTTPStatus.ACCEPTED
