import datetime
import json
import uuid
from http import HTTPStatus

from flask_restx import (Resource,
                         fields,
                         reqparse,)
import auth_lib
from config import (api,
                    redis_con,
                    name_space)
from models import (LoginPass,
                    UsersSessions,
                    UsersRoles,
                    Roles)
from keys import (generate_refresh_token,
                  redis_user_key)
from rate_limit import set_rate_limit


login_parser = reqparse.RequestParser()
login_parser.add_argument('token', type=str)
login_parser.add_argument('user_agent',
                          type=str,
                          required=False,
                          default='Unknown')


login_model = api.model('LoginModel', {'refresh_key': fields.String,})


@name_space.route('/yandex')
class LoginYandexService(Resource):

    @api.marshal_with(login_model,
                      code=HTTPStatus.ACCEPTED,
                      description='Accepted')
    @api.expect(login_parser)
    @api.response(HTTPStatus.UNAUTHORIZED, 'Unauthorized')
    @api.response(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')
    @set_rate_limit('yandex_login', 3)
    def post(self):
        args = login_parser.parse_args()
        token = args.get('token', None)
        if token is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable entity')

        user_info = auth_lib.yandex_get_user_info(token)
        if user_info is None:
            api.abort(HTTPStatus.UNAUTHORIZED, 'Unauthorized')

        user_rec = LoginPass.get_or_none(LoginPass.service == 'yandex',
                                         LoginPass.service_id == user_info['uid'])
        if user_rec is None:
            api.abort(HTTPStatus.UNAUTHORIZED, 'Unauthorized')

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
