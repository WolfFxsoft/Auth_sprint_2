"""
Check action key endpoint
"""


from http import HTTPStatus

from flask_restx import (Resource,
                         fields,
                         reqparse,)

from config import (api,
                    redis_con,
                    name_space)
from keys import (generate_jwt,
                  open_jwt,
                  redis_deny_key)

action_parser = reqparse.RequestParser()
action_parser.add_argument('action_key', type=str)

action_model = api.model('ActionModel',
                         {'action_key': fields.String})

@name_space.route('/action')
class ActionService(Resource):

    @api.marshal_with(action_model,
                      code=HTTPStatus.ACCEPTED,
                      description='Accepted')
    @api.expect(action_parser)
    @api.response(HTTPStatus.FORBIDDEN, 'Forbidden')
    @api.response(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable Entity')
    def post(self):
        args = action_parser.parse_args()
        action_key = args.get('action_key', None)
        if action_key is None:
            api.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Unprocessable Entity')
        if redis_con.get(redis_deny_key(action_key)):
            api.abort(HTTPStatus.FORBIDDEN, 'Forbiden')
        data = open_jwt(action_key)
        if data is None:
            api.abort(HTTPStatus.FORBIDDEN, 'Forbiden')
        data['try'] -= 1
        if data['try'] <0:
            api.abort(HTTPStatus.FORBIDDEN, 'Forbidden')

        return {'action_key': generate_jwt(data)}, HTTPStatus.ACCEPTED
