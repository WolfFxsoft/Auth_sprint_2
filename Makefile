.PHONY: list db_run db_stop db_bash db_create
ENV_PYTHON := env/bin/python3

DB_NAME := movies
DB_USER := postgres
DB_PASSWORD := password
DB_CONTAINER_NAME := postgres
DB_ENV := export DB_NAME=$(DB_NAME); export DB_USER=$(DB_USER); export DB_PASSWORD=$(DB_PASSWORD);


REDIS_CONTAINER_NAME := redis

AUTH_DOCKERFILE := auth_service/Dockerfile_auth
AUTH_IMAGE := auth_service_image
AUTH_TEST_DOCKERFILE := auth_service/tests/functional/Dockerfile_test
AUTH_TEST_IMAGE := auth_test_service_image
AUTH_TEST_CONTAINER := auth_test

USERS_DOCKERFILE := users_service/Dockerfile_users
USERS_IMAGE := users_service_image
USERS_TEST_DOCKERFILE := users_service/tests/functional/Dockerfile_test
USERS_TEST_IMAGE := users_test_service_image
USERS_TEST_CONTAINER := users_test

list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'


stage_run:
	docker run -d --rm \
	--name $(DB_CONTAINER_NAME) \
	-p 5432:5432 \
	--mount type=volume,src=db_data,dst=/var/lib/postgresql/data \
	--mount type=bind,src=$(shell pwd)/utils/create.sql,dst=/create.sql  \
	-e POSTGRES_PASSWORD=$(DB_PASSWORD) \
	postgres:13

	docker run -d --rm \
        --name $(REDIS_CONTAINER_NAME) \
        -p 6379:6379 \
        redis:6.2.6-alpine

	yes | cp -fi .env.test utils/.env.test
	-cd utils; ../$(ENV_PYTHON) wait_for_pg.py


stage_stop:
	-docker stop $(DB_CONTAINER_NAME)
	-docker stop $(REDIS_CONTAINER_NAME)


db_create:
	make stage_run
	docker exec -e POSTGRES_PASSWORD=password \
        $(DB_CONTAINER_NAME) \
        sh -c 'psql -U postgres -c "DROP DATABASE movies"; psql -U postgres -c "CREATE DATABASE movies;"; psql -U postgres -f create.sql movies'
	make stage_stop


auth_run_env:
	cd auth_service/src; export DB_NAME=movies; export AUTH_PORT=5001; ../../$(ENV_PYTHON) main.py

auth_build:
	docker build -f $(AUTH_DOCKERFILE) -t $(AUTH_IMAGE) .


auth_run_docker:
	make auth_build
	docker run -it --net=host --rm \
	--name auth_service \
	-e DB_NAME=$(DB_NAME) \
	-p 5001:5001 \
	$(AUTH_IMAGE)


users_run_env:
	cd users_service/src; export DB_NAME=movies; ../../$(ENV_PYTHON) main.py


users_build:
	docker build -f $(USERS_DOCKERFILE) -t $(USERS_IMAGE) .

users_run_docker:
	make users_build
	docker run -it --net=host --rm \
	--name users_service \
	-e DB_NAME=$(DB_NAME) \
	-p 5002:5002 \
	$(USERS_IMAGE)


run:
	make auth_build
	make users_build
	docker-compose --env-file .env.test --file docker-compose.prod.yml up -d

run_debug:
	make auth_build
	make users_build
	docker-compose --env-file .env.test --file docker-compose.dev.yml up

stop:
	docker-compose  --file docker-compose.prod.yml rm -fs



auth_test_build:
	docker build -f $(AUTH_TEST_DOCKERFILE) -t $(AUTH_TEST_IMAGE) .


auth_test:
	make auth_test_build
	docker run -it --net=host --rm \
	-e AUTH_TEST_URL=127.0.0.1:5001 \
	--name $(AUTH_TEST_CONTAINER) \
	$(AUTH_TEST_IMAGE)

auth_test_functional:
	make run
	make auth_test_build
	-make auth_test
	make stop


users_test_build:
	docker build -f $(USERS_TEST_DOCKERFILE) -t $(USERS_TEST_IMAGE) .


users_test:
	make users_test_build
	docker run -it --net=host --rm \
	-e AUTH_HOST=localhost \
	-e AUTH_PORT=5001 \
	-e USERS_TEST_URL=127.0.0.1:5002 \
	--name $(USERS_TEST_CONTAINER) \
	$(USERS_TEST_IMAGE)

users_test_functional:
	make run
	make users_test_build
	-make users_test
	make stop
