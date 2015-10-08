.PHONY: all clean test

SHELL = /bin/bash
PY_VER = $(shell python -c 'import sys; print(sys.version_info.major)')

py2:
	@if [[ $(PY_VER) != 2 ]]; then \
		echo -e "\n** Error: currently, MLTSP relies on Python 2.x **\n"; \
		exit 1; \
	fi

celery: py2
	@if [[ -z `ps ax | grep -v grep | grep -v make | grep celery_tasks` ]]; then \
		PYTHONPATH="./mltsp" celery worker -A celery_tasks -l info >>/tmp/celery.log 2>&1 & \
	else \
		echo "[Celery] is already running"; \
	fi

.DEFAULT_GOAL := all

all: py2
	python setup.py build_ext -i

clean:
	find . -name "*.so" | xargs rm

webapp: db py2 celery
	PYTHONPATH=. tools/launch_waitress.py

init: py2 db celery
	python start_mltsp.py --db-init --force

db:
	@if [[ -n `rethinkdb --daemon 2>&1 | grep "already in use"` ]]; then echo "[RethinkDB] is (probably) already running"; fi

external/casperjs: py2
	@tools/casper_install.sh

test_backend: db py2 celery
	nosetests -v mltsp

test_backend_no_docker: export MLTSP_NO_DOCKER=1
test_backend_no_docker: db py2 celery
	nosetests -v mltsp

test_frontend: external/casperjs py2 db celery
	@PYTHONPATH="." tools/casper_tests.py

test_frontend_no_docker: export MLTSP_NO_DOCKER=1
test_frontend_no_docker: export MLTSP_DEBUG_LOGIN=1
test_frontend_no_docker: external/casperjs py2 db celery
	@PYTHONPATH="." tools/casper_tests.py

test_entrypoint:
	mltsp --version

test: test_entrypoint test_backend test_frontend

test_no_docker: test_backend_no_docker test_frontend_no_docker

install: py2
	pip install -r requirements.txt
