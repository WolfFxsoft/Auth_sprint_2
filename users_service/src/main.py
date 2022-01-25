
import role
import user
import user_roles
import yandex

from config import app, config

if __name__ == '__main__':
    app.run(debug=True, host=config.users_host, port=config.users_port)
