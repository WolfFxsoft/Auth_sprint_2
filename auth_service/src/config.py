"""
Auth service config file
"""

import redis
from flask import Flask
from flask_restx import Api
from pydantic import (BaseSettings,
                      Field)

from jaeger_client import Config
from flask_opentracing import FlaskTracer


class AuthConfig(BaseSettings):
    auth_host: str = Field(default='0.0.0.0', env='AUTH_HOST')
    auth_port: int = Field(default=5000, env='AUTH_PORT')

    action_key_refres: int = Field(default=600, env='AUTH_ACTION_KEY_REFRESH')
    action_key_try: int = Field(default=20, env='AUTH_ACTION_KEY_TRY')

    db_host: str = Field(default='localhost', env='DB_HOST')
    db_name: str = Field(default='default', env='DB_NAME')
    db_user: str = Field(default='postgres', env='DB_USER')
    db_pass: str = Field(default='password', env='DB_PASSWORD')

    redis_host: str = Field(default='localhost', env='REDIS_HOST')
    redis_port: int = Field(default=6379, env='REDIS_PORT')

    jaeger_host: str = Field(default='localhost', env='JAEGER_HOST')
    jaeger_port: int = Field(default=6831, env='JAEGER_PORT')



config = AuthConfig()

DATABASE = f'postgresql://{config.db_user}:{config.db_pass}@{config.db_host}:5432/{config.db_name}'

app = Flask(__name__)
app.config.from_object(__name__)

api = Api(app, version='0.1', title='Auth API')

name_space = api.namespace('auth', "Authorization and authentication service")
redis_con = redis.Redis(host=config.redis_host, port=config.redis_port)

jaeger_config = {
    'sampler': {
        'type': 'const',
        'param': 1,
    },
    'local_agent': {
        'reporting_host': config.jaeger_host,
        'reporting_port': config.jaeger_port,
    },
}

def _setup_jaeger():
    setup_config = Config(
        config=jaeger_config,
        service_name='auth-api',
        validate=True,
    )
    return setup_config.initialize_tracer()

tracer = FlaskTracer(_setup_jaeger, app=app)
