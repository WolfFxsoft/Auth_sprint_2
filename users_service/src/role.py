"""
Roles CRUD operations
"""

import uuid
from http import HTTPStatus
from typing import Dict

import peewee
from flask_restx import (Resource,
                         fields,
                         reqparse)
from playhouse.shortcuts import model_to_dict

from models import Role
from config import api, role_ns
from utils import check_permissions


role_get_list_parser = reqparse.RequestParser()
role_get_list_parser.add_argument('action_key', type=str)

role_model_get = api.model("role_model_get",
                           {"role_id": fields.String,
                            "name_short": fields .String,
                            "description": fields.String,})


role_post_parser = reqparse.RequestParser()
role_post_parser.add_argument("name_short", type=str)
role_post_parser.add_argument("description", type=str)
role_post_parser.add_argument("action_key", type=str)

role_model_post = api.model("role_model_post", {'role_uuid': fields.String,})


role_delete_parser = reqparse.RequestParser()
role_delete_parser.add_argument("action_key", type=str)


def _role_rec_strip(role_dict: Dict) -> Dict:
    role_dict['name_short'] = role_dict['name_short'].strip()
    return role_dict


@role_ns.route("/")
class RoleHandler(Resource):

    @api.marshal_with(role_model_get, code=HTTPStatus.OK, as_list=True)
    @api.expect(role_get_list_parser)
    @api.doc(description="Get full roles list")
    @check_permissions(role_get_list_parser, 'role_m')
    def get(self):
        roles = list(map(_role_rec_strip, Role.select().dicts()))
        return roles, HTTPStatus.OK



    @api.marshal_with(role_model_post, code=HTTPStatus.CREATED, description="Created")
    @api.expect(role_post_parser)
    @api.response(HTTPStatus.CONFLICT, 'Conflict')
    @api.response(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')
    @api.doc(description="Create new role")
    @check_permissions(role_post_parser, 'role_m')
    def post(self):
        args = role_post_parser.parse_args()
        name_short = args.get('name_short', None)
        if name_short is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')

        test_name_short = Role.get_or_none(Role.name_short == args['name_short'])
        if test_name_short is not None:
            api.abort(HTTPStatus.CONFLICT, 'Conflict short_name not unique')

        role_id = uuid.uuid4()
        Role.create(role_id=role_id,
                    name_short=name_short,
                    description=args.get('description', ''))

        return {'role_uuid': role_id}, HTTPStatus.CREATED



@role_ns.route("/<string:role_uuid>")
class RoleUuidHandler(Resource):

    @api.marshal_with(role_model_get, code=HTTPStatus.OK, as_list=True)
    @api.expect(role_get_list_parser)
    @api.response(HTTPStatus.NOT_FOUND, 'Not found')
    @api.doc(description="Get role")
    @check_permissions(role_get_list_parser, 'role_m')
    def get(self, role_uuid):
        try:
            role = Role.get(Role.role_id == role_uuid)
        except (peewee.DoesNotExist, peewee.DataError):
            api.abort(HTTPStatus.NOT_FOUND, 'Not found')
        return _role_rec_strip(model_to_dict(role))


    @api.expect(role_delete_parser)
    @api.response(HTTPStatus.OK, 'Ok')
    @api.response(HTTPStatus.NOT_FOUND, 'Not found')
    @api.doc(description="Delete role")
    @check_permissions(role_delete_parser, 'role_m')
    def delete(self, role_uuid):
        try:
            role = Role.get(Role.role_id == role_uuid)
        except (peewee.DoesNotExist, peewee.DataError):
            api.abort(HTTPStatus.NOT_FOUND, 'Not found')
        try:
            role.delete_instance()
        except (peewee.DatabaseError, peewee.IntegrityError):
            api.abbort(HTTPStatus.CONFLICT, 'Loocks by ForeignKey')
        return '', HTTPStatus.OK
