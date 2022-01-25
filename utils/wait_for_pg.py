
import os
import time
import psycopg2
import pydantic

TRYS = 20

class DBConfig(pydantic.BaseSettings):
    """ get postgresql connection options """
    host: str = pydantic.Field(default='127.0.0.1', env='DB_HOST')
    name: str = pydantic.Field(env='DB_NAME')
    user: str = pydantic.Field(env='DB_USER')
    password: str = pydantic.Field(env='DB_PASSWORD')

    class Config:
        env_file = '.env.test'
        env_file_encoding = 'utf-8'


def main():
    print('Waiting postgresql')
    db_conf = DBConfig()
    trys = 0
    while trys <= TRYS:
        try:
            conn = psycopg2.connect(host=db_conf.host,
                                    dbname=db_conf.name,
                                    user=db_conf.user,
                                    password=db_conf.password)
            conn.close()
            print('Postgresql ready !')
            break
        except psycopg2.Error:
            print('Try connect ...')
            time.sleep(1)
            trys += 1


if __name__ == '__main__':
    main()
