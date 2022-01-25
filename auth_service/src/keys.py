"""
functino and classes for keys manipulation
"""
import dataclasses
import datetime
import secrets
import uuid

import jwt

from config import config

REFRESH_TOKEN_SIZE = 32
TMP_JWT_KEY = "secret"


@dataclasses.dataclass
class KeyItem:
    key: str
    kill_at: datetime.datetime



class MovingJwtKeys():

    def __init__(self, now=None):
        self.first_key = None
        self.second_key = None
        if now is None:
            now = datetime.datetime.now()
        self._refresh_keys(now)


    def _refresh_keys(self, now):
        if self.second_key and self.second_key.kill_at <= now:
            if self.first_key and self.first_key.kill_at <= now:
                self.second_key = None
            else:
                self.second_key = self.first_key
                self.first_key = None

        if self.first_key is None:
            kill_at = now + datetime.timedelta(seconds=config.action_key_refres)
            self.first_key = KeyItem(key=str(uuid.uuid4()),
                                     kill_at=kill_at)

        if self.second_key is None:
            kill_at = now + datetime.timedelta(seconds=config.action_key_refres * 2)
            self.second_key = KeyItem(key=str(uuid.uuid4()),
                                      kill_at=kill_at)



    def __call__(self, now=None):
        if now is None:
            now = datetime.datetime.now()
        self._refresh_keys(now)
        return self.first_key.key, self.second_key.key


def redis_user_key(refresh_key):
    """ generate user key based on refresh_key for redis """
    return f"user:{refresh_key}"

def redis_deny_key(action_key):
    """ generate key for deny action_keys"""
    return f"deny:{action_key}"


def generate_refresh_token():
    """ single place for refresh key generator """
    return secrets.token_urlsafe(REFRESH_TOKEN_SIZE)


moving_jwt_keys = MovingJwtKeys()


def generate_jwt(data):
    """ generate jwt action key using moving secret key"""
    key, _ = moving_jwt_keys()
    return jwt.encode(data, key, algorithm="HS256")


def open_jwt(jwt_key):
    """ try to open jwt action key using current moving secret key"""
    first_key, second_key = moving_jwt_keys()
    try:
        return jwt.decode(jwt_key, first_key, algorithms=["HS256",])
    except jwt.DecodeError:
        try:
            return jwt.decode(jwt_key, second_key, algorithms=["HS256",])
        except jwt.DecodeError:
            return None
