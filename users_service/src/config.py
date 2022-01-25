
from flask import Flask
from flask_restx import Api
from pydantic import (BaseSettings,
                      Field)

from jaeger_client import Config
from flask_opentracing import FlaskTracer


class UsersConfig(BaseSettings):
    users_host: str = Field(default='0.0.0.0', env='USERS_HOST')
    users_port: int = Field(default=5002, env='USERS_PORT')

    auth_host: str = Field(default='0.0.0.0', env='AUTH_HOST')
    auth_port: int = Field(default=5001, env='AUTH_PORT')

    db_host: str = Field(default='localhost', env='DB_HOST')
    db_name: str = Field(default='default', env='DB_NAME')
    db_user: str = Field(default='postgres', env='DB_USER')
    db_pass: str = Field(default='password', env='DB_PASSWORD')

    jaeger_host: str = Field(default='localhost', env='JAEGER_HOST')
    jaeger_port: int = Field(default=6831, env='JAEGER_PORT')


config = UsersConfig()

DATABASE = f'postgresql://{config.db_user}:{config.db_pass}@{config.db_host}:5432/{config.db_name}'

app = Flask(__name__)
app.config.from_object(__name__)

api = Api(
    app,
    version="1.0",
    title="User Auth API",
    description="A simple user auth API",
)

role_ns = api.namespace("role", description="Roles crud operations")
user_ns = api.namespace("user", description="User data crud operations")

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
        service_name='users-api',
        validate=True,
    )
    return setup_config.initialize_tracer()

tracer = FlaskTracer(_setup_jaeger, app=app)
