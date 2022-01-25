from peewee import (CharField,
                    TextField,
                    UUIDField,
                    DateTimeField)
from playhouse.flask_utils import FlaskDB

from config import app

db_wrapper = FlaskDB(app)

class BaseModel(db_wrapper.Model):

    class Meta:
        schema = 'users_auth'



class LoginPass(BaseModel):

    user_id = UUIDField(primary_key=True)
    login = CharField(max_length=40, null=False, unique = True)
    password = CharField(max_length=64, null=False)
    service = TextField()
    service_id = TextField()

    class Meta:
        table_name = 'login_pass'



class UsersData(BaseModel):

    user_id = UUIDField(primary_key=True)
    first_name = CharField(max_length=40, null=False)
    second_name = CharField(max_length=40, null=False)

    class Meta:
        table_name = 'users_data'



class Role(BaseModel):
    role_id = UUIDField(primary_key=True)
    name_short = CharField(unique=True)
    description = TextField()

    class Meta:
        table_name = 'roles'



class UsersRole(BaseModel):
    role_id = UUIDField(primary_key=True)
    user_id = UUIDField(unique=True)

    class Meta:
        table_name = 'users_roles'


class UsersSessions(BaseModel):
    id = UUIDField(primary_key=True)
    user_id = UUIDField()
    start_at = DateTimeField()
    user_agent = CharField(max_length=100)

    class Meta:
        table_name = 'users_sessions'
