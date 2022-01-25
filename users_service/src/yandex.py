"""
Yandex special endpoints
"""

import uuid
from http import HTTPStatus
from typing import Dict

import peewee
from flask_restx import(Resource,
                        fields,
                        reqparse)



import auth_lib
from config import api, user_ns
from utils import check_permissions
from models import (LoginPass,
                    UsersData)



action_key_parser = reqparse.RequestParser()
action_key_parser.add_argument('action_key', type=str)

token_parser = reqparse.RequestParser()
token_parser.add_argument('action_key', type=str)
token_parser.add_argument('token', type=str)

password_parser = reqparse.RequestParser()
password_parser.add_argument('action_key', type=str)
password_parser.add_argument('password', type=str)

user_model_uuid = api.model('User UUID Model', {'user_uuid': fields.String,})

@user_ns.route('/yandex')
class UserYandesHandler(Resource):

    @api.marshal_with(user_model_uuid, code=HTTPStatus.CREATED)
    @api.expect(token_parser)
    @api.response(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')
    @api.response(HTTPStatus.CONFLICT, 'Conflict')
    @api.response(HTTPStatus.UNAUTHORIZED, 'Unauthorized')
    @api.doc(description="Create new User based on yandex ID API")
    @check_permissions(token_parser, 'user_m')
    def post(self):
        args = token_parser.parse_args()
        token = args.get('token', None)
        if token is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')
        user_info = auth_lib.yandex_get_user_info(token)
        if user_info is None:
            api.abort(HTTPStatus.UNAUTHORIZED, 'Unauthorized')

        user_uuid = str(uuid.uuid4())
        service_id = user_info.get('uid', None)
        if service_id is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')
        login = user_info.get('login', None)
        if service_id is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')
        full_name = user_info.get('name', None)
        if service_id is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')
        first_name = ' '.join(full_name.split()[:1])
        second_name = ' '.join(full_name.split()[1:])

        LoginPass.create(user_id=user_uuid,
                         login=login,
                         password=None,
                         service='yandex',
                         service_id=service_id)
        UsersData.create(user_id=user_uuid,
                         first_name=first_name,
                         second_name=second_name)


        return {'user_uuid': user_uuid}, HTTPStatus.CREATED


@user_ns.route('/yandex/<string:user_uuid>')
class UserYandexIdHandler(Resource):

    @api.marshal_with(user_model_uuid, code=HTTPStatus.OK)
    @api.expect(password_parser)
    @api.response(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')
    @api.response(HTTPStatus.NOT_FOUND, 'Not found')
    @api.doc('Reconect user to self authorization')
    @check_permissions(password_parser, 'user_m')
    def delete(self, user_uuid):
        args = password_parser.parse_args()
        password = args.get('password', None)
        if password is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')
        login_pass_rec = LoginPass.get_or_none(LoginPass.user_id == user_uuid)
        if login_pass_rec is None:
            api.asbort(HTTPStatus.NOT_FOUND, 'Not found')
        login_pass_rec.password = auth_lib.pass_hasher(password)
        login_pass_rec.service = 'self'
        login_pass_rec.service_id = None
        login_pass_rec.save()

        return HTTPStatus.OK
