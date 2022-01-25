7 спринт

/user/yandex (post) принимает токен берет данные из Яндекса и создает учетную запись
/user/yandex/<user_uuid> принимает пароль и переключает пользователя на авторизацию сервиса

/auth/yandex вход в систему по токену
* swagger файл авторизации auth_swagger.json (http://localhost:5001/)
  swagger файл управления пользователями user_swagger.json (http://localhost:5002/)

* Rate limit
  * все endpoint за исключением yandex ограничены в конфигурации nginx через limit_req
  * отдельно ограничены обращения для авторизации в яндекс в декоратором

* Партицирование добавлено на таблицу login_pass по enum полю провайдера авторизации
  файл utils/create.sql

6 спринт
* подготовка базы для запуска проекта make db_create
* запустить проект make run
* запустить проект без отключение консоли make run_debug
* остановить make stop

* тест сервиса авторизации make auth_test_functional
* тесе сервиса пользователей make users_test_functional


Процесс авторизаций (swagger http://localhost:5001/):
/auth/login  передается логин пароль получаем refresh_key
/auth/refresh передаем refresh_key и роль получаем временный ключ на данную роль action_key
/auth/action проверка action_key.


Управление пользователями (swagger http://localhost:5002/)
/role - управление ролями
/user - управление пользователями
