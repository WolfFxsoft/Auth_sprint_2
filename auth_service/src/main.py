
import login
import refresh
import action
import yandex

from config import app, config

if __name__ == '__main__':
    app.run(debug=True, host=config.auth_host, port=config.auth_port)
