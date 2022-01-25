"""
DB Models
"""

import peewee
from playhouse.flask_utils import FlaskDB

from config import app


db_wrapper = FlaskDB(app)


class LoginPass(db_wrapper.Model):
    user_id = peewee.UUIDField(primary_key=True)
    login = peewee.CharField(max_length=40)
    password = peewee.CharField(max_length=64)
    service = peewee.TextField()
    service_id = peewee.TextField()

    class Meta:
        table_name = 'login_pass'
        schema = 'users_auth'


class UsersSessions(db_wrapper.Model):
    id = peewee.UUIDField(primary_key=True)
    user_id = peewee.UUIDField()
    start_at = peewee.DateTimeField()
    user_agent = peewee.CharField(max_length=100)

    class Meta:
        table_name = 'users_sessions'
        schema = 'users_auth'



class Roles(db_wrapper.Model):
    role_id = peewee.UUIDField(primary_key=True)
    name_short = peewee.CharField(max_length=15)
    description = peewee.TextField()

    class Meta:
        table_name = 'roles'
        schema = 'users_auth'



class UsersRoles(db_wrapper.Model):
    user_id = peewee.UUIDField()
    role_id = peewee.UUIDField()

    class Meta:
        table_name = 'users_roles'
        schema = 'users_auth'
