.PHONY: all clean test

SHELL = /bin/bash
PY_VER = $(shell python -c 'import sys; print(sys.version_info.major)')
CLEAN_TEST_CONFIG = $(shell rm -f mltsp-_test_.yaml)

celery:
	@if [[ -z `ps ax | grep -v grep | grep -v make | grep celery_tasks` ]]; then \
		PYTHONPATH="./mltsp" celery worker -A celery_tasks -l info >>/tmp/celery.log 2>&1 & \
	else \
		echo "[Celery] is already running"; \
	fi

.DEFAULT_GOAL := all

all:
	python setup.py build_ext -i

clean: clean_test_config
	find . -name "*.so" | xargs rm -f

clean_test_config:
	rm -f mltsp-_test_.yaml

webapp: db celery
	PYTHONPATH=. $(MAKE) -C web_client

init: db celery
	mltsp --db-init --force

db:
	@if [[ -n `rethinkdb --daemon 2>&1 | grep "already in use"` ]]; then echo "[RethinkDB] is (probably) already running"; fi

external/casperjs:
	@tools/casper_install.sh


test_backend: db celery
	nosetests -v mltsp

test_backend_no_docker: db celery | clean_test_config
	echo -e "testing:\n    no_docker: 1" > "mltsp-_test_.yaml"
	nosetests -v mltsp

test_frontend: external/casperjs db celery | clean_test_config
	echo -e "testing:\n    disable_auth: 1" > "mltsp-_test_.yaml"
	@PYTHONPATH="." tools/casper_tests.py

test_frontend_no_docker: external/casperjs db celery | clean_test_config
	echo -e "testing:\n    no_docker: 1" > "mltsp-_test_.yaml"
	echo -e "testing:\n    disable_auth: 1" >> "mltsp-_test_.yaml"
	@PYTHONPATH="." tools/casper_tests.py

test_entrypoint:
	mltsp --version

test: test_entrypoint test_backend test_frontend

test_no_docker: test_backend_no_docker test_frontend_no_docker

install:
	pip install -r requirements.txt

html:
	pip install -q sphinx -r requirements.readthedocs.txt
	export SPHINXOPTS=-W; make -C doc html
