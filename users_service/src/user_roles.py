"""
Users CRUD operations
"""

from http import HTTPStatus
from operator import itemgetter
from typing import Dict

from flask_restx import(Resource,
                        fields,
                        reqparse)

from config import api, user_ns
from utils import check_permissions
from models import (LoginPass,
                    UsersRole,
                    Role)


action_key_parser = reqparse.RequestParser()
action_key_parser.add_argument('action_key', type=str)

role_uuid_parser =  reqparse.RequestParser()
role_uuid_parser.add_argument('action_key', type=str)
role_uuid_parser.add_argument('role_uuid', type=str)

users_roles_model = api.model("User's roles Model",
                              {'role_id': fields.String,
                               'name_short': fields.String})

def _role_rec_srtip(rec: Dict) -> Dict:
    rec['name_short'] = rec['name_short'].strip()
    return rec

@user_ns.route('/role/<string:user_uuid>')
class UserRoleHandler(Resource):

    @api.marshal_with(users_roles_model, code=HTTPStatus.OK, as_list=True)
    @api.expect(action_key_parser)
    @api.response(HTTPStatus.NOT_FOUND, 'Not found')
    @api.doc(description="Get user's roles")
    @check_permissions(action_key_parser, "user_m")
    def get(self, user_uuid):
        test_user_rec = LoginPass.get_or_none(LoginPass.user_id == user_uuid)
        if test_user_rec is None:
            api.abort(HTTPStatus.NOT_FOUND, 'Not found')

        users_roles = UsersRole.\
            select(UsersRole.role_id).\
            where(UsersRole.user_id == user_uuid).\
            tuples()
        users_roles = list(map(itemgetter(0), users_roles))

        roles = Role.\
            select(Role.role_id, Role.name_short).\
            where(Role.role_id.in_(users_roles)).\
            dicts()
        roles = list(map(_role_rec_srtip, roles))
        return roles, HTTPStatus.OK



    @api.expect(role_uuid_parser)
    @api.response(HTTPStatus.CREATED, 'Created')
    @api.response(HTTPStatus.CONFLICT, 'Conflict')
    @api.response(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')
    @api.response(HTTPStatus.NOT_FOUND, 'Not found')
    @api.doc(description="Append new role to user")
    @check_permissions(role_uuid_parser, 'user_m')
    def post(self, user_uuid):
        test_user_rec = LoginPass.get_or_none(LoginPass.user_id == user_uuid)
        if test_user_rec is None:
            api.abort(HTTPStatus.NOT_FOUND, 'Not found')

        args = role_uuid_parser.parse_args()
        role_uuid = args.get('role_uuid', None)
        if role_uuid is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')

        test_role = Role.get_or_none(Role.role_id == role_uuid)
        if test_role is None:
            api.abort(HTTPStatus.NOT_FOUND, 'Not found')

        test_user_role = UsersRole.get_or_none(UsersRole.user_id == user_uuid,
                                               UsersRole.role_id == role_uuid)
        if test_user_role is not None:
            api.abort(HTTPStatus.CONFLICT, 'Conflict')

        UsersRole.create(user_id=user_uuid, role_id=role_uuid)

        return '', HTTPStatus.CREATED


    @api.expect(role_uuid_parser)
    @api.response(HTTPStatus.CREATED, 'OK')
    @api.response(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')
    @api.response(HTTPStatus.NOT_FOUND, 'Not found')
    @api.doc(description="Delete user role")
    @check_permissions(role_uuid_parser, 'user_m')
    def delete(self, user_uuid):
        test_user_rec = LoginPass.get_or_none(LoginPass.user_id == user_uuid)
        if test_user_rec is None:
            api.abort(HTTPStatus.NOT_FOUND, 'Not found')

        args = role_uuid_parser.parse_args()
        role_uuid = args.get('role_uuid', None)
        if role_uuid is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')

        user_role = UsersRole.get_or_none(UsersRole.user_id == user_uuid,
                                          UsersRole.role_id == role_uuid)
        if user_role is None:
            api.abort(HTTPStatus.NOT_FOUND, 'Not found')

        user_role.delete_instance()

        return '', HTTPStatus.OK
