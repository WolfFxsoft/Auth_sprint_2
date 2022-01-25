
-- CREATE DATABASE movies;
CREATE SCHEMA IF NOT EXISTS users_auth;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


CREATE TYPE users_auth.auth_type AS ENUM ('self', 'yandex');

CREATE TABLE IF NOT EXISTS users_auth.login_pass (
       user_id uuid,
       login char(40) NOT NULL,
       password char(64),
       service users_auth.auth_type NOT NULL DEFAULT 'self',
       service_id text) PARTITION BY list (service);

CREATE TABLE IF NOT EXISTS users_auth.login_pass_self PARTITION OF users_auth.login_pass FOR VALUES IN ('self');
CREATE TABLE IF NOT EXISTS users_auth.login_pass_yandex PARTITION OF users_auth.login_pass FOR VALUES IN ('yandex');

CREATE UNIQUE INDEX IF NOT EXISTS unique_login_pass_login_self_idx ON users_auth.login_pass_self (user_id);
CREATE UNIQUE INDEX IF NOT EXISTS unique_login_pass_login_yandex_idx ON users_auth.login_pass_yandex (user_id);


CREATE TABLE IF NOT EXISTS users_auth.users_data (
       user_id uuid PRIMARY KEY,
       first_name char(40) NOT NULL,
       second_name char(40) NOT NULL);
-- тут можно добавить поля под данные пользователей

CREATE TABLE IF NOT EXISTS users_auth.roles (
       role_id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
       name_short char(15),
       description text);


CREATE TABLE IF NOT EXISTS users_auth.users_roles(
       user_id uuid NOT NULL,
       role_id uuid NOT NULL REFERENCES users_auth.roles(role_id) ON DELETE CASCADE,
       PRIMARY KEY (user_id, role_id));


CREATE TABLE IF NOT EXISTS users_auth.users_sessions(
       id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
       user_id uuid,
       start_at timestamp with time zone,
       user_agent varchar(100))
