"""
Utility functions
"""


from http import HTTPStatus

import jwt
import requests

from config import api, config


AUTH_URL = f"http://{config.auth_host}:{config.auth_port}/auth/action"


def check_permissions(parser, role_permission: str):

    def inner_decorator(func):

        def wrapper(*args, **kwargs):
            parser_args = parser.parse_args()
            action_key = parser_args.get('action_key', None)
            if action_key is None:
                api.abort(HTTPStatus.FORBIDDEN, 'Forbidden')
            try:
                action_key_body = jwt.decode(action_key,
                                             options={"verify_signature": False})
            except jwt.DecodeError:
                api.abort(HTTPStatus.FORBIDDEN, 'Forbidden')
            if 'role' not in action_key_body:
                api.abort(HTTPStatus.FORBIDDEN, 'Forbidden')
            user_role = action_key_body["role"]
            if user_role != role_permission:
                api.abort(HTTPStatus.FORBIDDEN, 'Forbidden')

            response = requests.post(AUTH_URL,
                                     data={'action_key': action_key})
            if response.status_code != HTTPStatus.ACCEPTED:
                api.abort(HTTPStatus.FORBIDDEN, 'Forbidden')
            return func(*args, **kwargs)

        return wrapper

    return inner_decorator
