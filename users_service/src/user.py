"""
Users CRUD operations
"""

import uuid
from http import HTTPStatus
from typing import Dict

import peewee
from flask_restx import(Resource,
                        fields,
                        reqparse)

from config import api, user_ns
from auth_lib import pass_hasher
from utils import check_permissions
from models import (LoginPass,
                    UsersData,
                    UsersRole,
                    UsersSessions)


action_key_parser = reqparse.RequestParser()
action_key_parser.add_argument('action_key', type=str)

user_full_parser = reqparse.RequestParser()
user_full_parser.add_argument('action_key', type=str)
user_full_parser.add_argument('login', type=str)
user_full_parser.add_argument('password', type=str)
user_full_parser.add_argument('first_name', type=str)
user_full_parser.add_argument('second_name', type=str)

user_data_parser = reqparse.RequestParser()
user_data_parser.add_argument('action_key', type=str)
user_data_parser.add_argument('first_name', type=str)
user_data_parser.add_argument('second_name', type=str)

user_password_parser = reqparse.RequestParser()
user_password_parser.add_argument('action_key', type=str)
user_password_parser.add_argument('password', type=str)

user_model_uuid = api.model('User UUID Model', {'user_uuid': fields.String,})

user_model_get = api.model('User Model',
                           {'user_id': fields.String,
                            'login': fields.String,
                            'service': fields.String,
                            'first_name': fields.String,
                            'second_name': fields.String})


def _user_rec_strip(rec: Dict) -> Dict:
    rec['login'] = rec['login'].strip()
    rec['first_name'] = rec['first_name'].strip() if rec['first_name']  else ''
    rec['second_name'] = rec['second_name'].strip() if rec['second_name']  else ''
    return rec


@user_ns.route('/')
class UserHandler(Resource):

    @api.marshal_with(user_model_get, code=HTTPStatus.OK, as_list=True)
    @api.expect(action_key_parser)
    @api.doc(description="Get full users list")
    @check_permissions(action_key_parser, 'user_m')
    def get(self):
        users = LoginPass.\
            select(LoginPass.user_id,
                   LoginPass.login,
                   LoginPass.service,
                   UsersData.first_name,
                   UsersData.second_name).\
            join(UsersData,
                 peewee.JOIN.LEFT_OUTER,
                 on=(LoginPass.user_id == UsersData.user_id)).\
            dicts()
        users = list(map(_user_rec_strip, users))
        return users, HTTPStatus.OK


    @api.marshal_with(user_model_uuid, code=HTTPStatus.CREATED)
    @api.expect(user_full_parser)
    @api.response(HTTPStatus.CONFLICT, 'Conflict')
    @api.response(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')
    @api.doc(description="Create new User")
    @check_permissions(action_key_parser, 'user_m')
    def post(self):
        args = user_full_parser.parse_args()
        login = args.get('login', None)
        password = args.get('password', None)

        if login is None or password is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')

        test_login = LoginPass.get_or_none(LoginPass.login == login)
        if test_login is not None:
            api.abort(HTTPStatus.CONFLICT, 'Conflict')

        user_id = str(uuid.uuid4())
        password = pass_hasher(password)

        LoginPass.create(user_id=user_id,
                         login=login,
                         password=password)
        UsersData.create(user_id=user_id,
                         first_name=args.get('first_name', ''),
                         second_name=args.get('second_name'))
        return {'user_uuid': user_id}, HTTPStatus.OK




@user_ns.route('/<string:user_uuid>')
class UserIdHandler(Resource):

    @api.marshal_with(user_model_get, code=HTTPStatus.OK)
    @api.expect(action_key_parser)
    @api.response(HTTPStatus.NOT_FOUND, 'Not found')
    @api.doc(description='Get user by user_uuid')
    @check_permissions(action_key_parser, 'user_m')
    def get(self, user_uuid):
        users = LoginPass.\
            select(LoginPass.user_id,
                   LoginPass.login,
                   LoginPass.service,
                   UsersData.first_name,
                   UsersData.second_name).\
            join(UsersData,
                 peewee.JOIN.LEFT_OUTER,
                 on=(LoginPass.user_id == UsersData.user_id)).\
            where(LoginPass.user_id == user_uuid).\
            dicts()
        users = list(map(_user_rec_strip, users))
        if len(users) == 0:
            api.abort(HTTPStatus.NOT_FOUND, 'Not found')

        return users[0], HTTPStatus.OK


    @api.expect(user_data_parser)
    @api.response(HTTPStatus.OK, 'Ok')
    @api.response(HTTPStatus.NOT_FOUND, 'Not found')
    @api.doc(description="Change user data")
    @check_permissions(user_data_parser, 'user_m')
    def put(self, user_uuid):
        login_pass_rec = LoginPass.get_or_none(LoginPass.user_id == user_uuid)
        if login_pass_rec is None:
            api.abort(HTTPStatus.NOT_FOUND, 'Not found')
        args = user_data_parser.parse_args()
        UsersData.\
            insert(user_id=user_uuid,
                   first_name=args.get('first_name', ''),
                   second_name=args.get('second_name', '')).\
            on_conflict(conflict_target=[UsersData.user_id],
                        preserve=[UsersData.user_id],
                        update={'first_name': args.get('first_name', ''),
                                'second_name': args.get('second_name')}).\
            execute()
        return '', HTTPStatus.OK


    @api.expect(action_key_parser)
    @api.response(HTTPStatus.OK, 'Ok')
    @api.response(HTTPStatus.NOT_FOUND, 'Not found')
    @api.response(HTTPStatus.CONFLICT, 'Conflict')
    @api.doc(description="Delete user by user_uuid")
    @check_permissions(action_key_parser, 'user_m')
    def delete(self, user_uuid):
        login_pass_rec = LoginPass.get_or_none(LoginPass.user_id == user_uuid)
        if login_pass_rec is None:
            api.abort(HTTPStatus.NOT_FOUND, 'Not found')

        user_data_rec = UsersData.get_or_none(UsersData.user_id == user_uuid)
        if user_data_rec is not None:
            try:
                user_data_rec.delete_instance()
            except (peewee.DataError, peewee.IntegrityError):
                api.abort(HTTPStatus.CONFLICT, 'Locks by foreignkey')

        UsersRole.delete().where(UsersRole.user_id == user_uuid).execute()
        UsersSessions.delete().where(UsersSessions.user_id == user_uuid).execute()

        try:
            login_pass_rec.delete_instance()
        except (peewee.DataError, peewee.IntegrityError):
            api.abort(HTTPStatus.CONFLICT, 'Locks by foreignkey')

        return '', HTTPStatus.OK



@user_ns.route("/password/<string:user_uuid>")
class UserPasswordHandler(Resource):

    @api.expect(user_password_parser)
    @api.response(HTTPStatus.OK, 'Ok')
    @api.response(HTTPStatus.NOT_FOUND, 'Not found')
    @api.response(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')
    @api.doc(description="Change user data")
    @check_permissions(user_password_parser, 'user_m')
    def put(self, user_uuid):
        login_pass_rec = LoginPass.get_or_none(LoginPass.user_id == user_uuid)
        if login_pass_rec is None:
            api.abort(HTTPStatus.NOT_FOUND, 'Not found')

        args = user_password_parser.parse_args()
        password = args.get('password', None)
        if password is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')

        login_pass_rec.password = pass_hasher(password)
        login_pass_rec.save()

        return '', HTTPStatus.OK
