
import uuid
from http import HTTPStatus

from config import (api,
                    redis_con)

TIME_LIVING = 1

def set_rate_limit(prefix: str, limit: int):
    def decorator(func):

        def wrapper(*args, **kwargs):
            keys = list(redis_con.scan_iter(f"rate:{prefix}*"))
            if len(keys) > limit:
                api.abort(HTTPStatus.TOO_MANY_REQUESTS, 'Too many requests')
            postfix = str(uuid.uuid4())
            key = f"rate:{prefix}:{postfix}"
            redis_con.set(key, prefix, ex=TIME_LIVING)
            return func(*args, **kwargs)

        return wrapper
    return decorator
