
import json
from http import HTTPStatus

from flask_restx import (Resource,
                         fields,
                         reqparse,)

from config import (api,
                    redis_con,
                    config,
                    name_space)
from keys import (generate_jwt,
                  redis_user_key)


refresh_parser = reqparse.RequestParser()
refresh_parser.add_argument('refresh_key', type=str)
refresh_parser.add_argument('role', type=str)

refresh_model = api.model('RefreshModel',
                          {'refresh_key': fields.String,
                           'action_key': fields.String})


@name_space.route('/refresh', endpoint='refresh')
class RefreshService(Resource):

    @api.marshal_with(refresh_model, code=HTTPStatus.OK, description='Accepted')
    @api.expect(refresh_parser)
    @api.response(HTTPStatus.UNAUTHORIZED, 'Unauthorized')
    @api.response(HTTPStatus.FORBIDDEN, 'Forbidden')
    @api.response(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable Entity')
    def post(self):
        args = refresh_parser.parse_args()
        refresh_key = args.get('refresh_key', None)
        if refresh_key is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable Entity')

        user_rec = redis_con.get(redis_user_key(refresh_key))
        if user_rec is None:
            api.abort(HTTPStatus.UNAUTHORIZED, 'Unauthorized')
        user_rec = json.loads(user_rec)

        role = args.get('role', None)
        if role is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable Entity')
        if role in user_rec['roles']:
            return {'refresh_key': refresh_key,
                    'action_key': generate_jwt({'role': role,
                                                'try': config.action_key_try})
                    }, HTTPStatus.ACCEPTED
        api.abort(HTTPStatus.FORBIDDEN, 'Forbiden')
