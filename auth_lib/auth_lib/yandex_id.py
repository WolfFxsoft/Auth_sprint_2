"""
получить отладочный токен
https://oauth.yandex.ru/authorize?response_type=token&client_id=572f17c671b742f9a958963d2459171a
"""

import uuid
from http import HTTPStatus
from typing import Dict, Optional

import requests
import jwt


def yandex_get_user_info(token:str) -> Optional[Dict]:
    try:
        secret = str(uuid.uuid4())[::3]
        result = requests.get('https://login.yandex.ru/info',
                              params={'format': 'jwt',
                                      'jwt_secret': secret},
                              headers={'Authorization': f'OAuth {token}'})
        if result.status_code == HTTPStatus.OK:
            decode_dict = jwt.decode(result.text, secret, algorithms=['HS256',])
            return decode_dict
        if result.status_code == HTTPStatus.UNAUTHORIZED:
            return None
    except requests.ConnectionError:
        return None
