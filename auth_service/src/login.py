
import datetime
import json
import uuid
from http import HTTPStatus

from flask_restx import (Resource,
                         fields,
                         reqparse,)

import auth_lib
from config import (config,
                    api,
                    redis_con,
                    name_space)
from models import (LoginPass,
                    UsersSessions,
                    Roles,
                    UsersRoles)
from keys import (generate_refresh_token,
                  redis_user_key,
                  redis_deny_key)




login_parser = reqparse.RequestParser()
login_parser.add_argument('login', type=str)
login_parser.add_argument('password', type=str)
login_parser.add_argument('user_agent',
                          type=str,
                          required=False,
                          default='Unknown')

login_model = api.model('LoginModel', {'refresh_key': fields.String,})


@name_space.route('/login', endpoint='login')
class LoginService(Resource):

    @api.marshal_with(login_model,
                      code=HTTPStatus.ACCEPTED,
                      description='Accepted')
    @api.expect(login_parser)
    @api.response(HTTPStatus.UNAUTHORIZED, 'Unauthorized')
    def post(self):
        """ try login """
        args = login_parser.parse_args()
        login = args.get('login', None)
        if login is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')
        password = args.get('password', None)
        if password is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')
        hashed_pass = auth_lib.pass_hasher(password)

        user_rec = LoginPass.get_or_none(LoginPass.login == login,
                                         LoginPass.password == hashed_pass,
                                         LoginPass.service == 'self')
        if user_rec is None:
            api.abort(HTTPStatus.UNAUTHORIZED, f'Unauthorized')

        # session start record
        UsersSessions.insert(id=uuid.uuid4(),
                             user_id=user_rec.user_id,
                             start_at=datetime.datetime.now(),
                             user_agent=args.get('user_agent',
                                                 'Unknown')).execute()
        # get user roles
        role_ids = UsersRoles.select(UsersRoles.role_id).\
            where(UsersRoles.user_id == user_rec.user_id).\
            tuples()
        role_ids = map(lambda x: str(x[0]), role_ids)

        roles = Roles.select(Roles.name_short).\
            where(Roles.role_id.in_(list(role_ids))).\
            tuples()
        roles = map(lambda x: x[0].strip(), roles)

        refresh_key = generate_refresh_token()

        redis_con.set(redis_user_key(refresh_key),
                      json.dumps({'user_id': str(user_rec.user_id),
                                  'roles': list(roles)}))

        return {'refresh_key': refresh_key}, HTTPStatus.ACCEPTED


logout_parser = reqparse.RequestParser()
logout_parser.add_argument('refresh_key', type=str)
logout_parser.add_argument('action_key', type=str)

@name_space.route('/logout')
class LogoutService(Resource):

    @api.expect(logout_parser)
    @api.response(HTTPStatus.OK, 'Ok')
    @api.response(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable Entity')
    def post(self):
        args = logout_parser.parse_args()
        refresh_key = args.get('refresh_key', None)
        if refresh_key is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable Entity')
        action_key = args.get('action_key', None)
        if action_key is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable Entity')

        redis_con.delete(redis_user_key(refresh_key))
        # 3 * refresh cover action_key life circle,
        # life circle only 2 refresh period
        redis_con.set(redis_deny_key(action_key),
                      action_key,
                      ex=config.action_key_refres * 3)
        return {}, HTTPStatus.OK
