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

clean:
	find . -name "*.so" | xargs rm -f

webapp: db celery
	@rm -f mltsp-_test_.yaml
	PYTHONPATH=. $(MAKE) -C web_client

init: db celery
	mltsp --db-init --force

db:
	@if [[ -n `rethinkdb --daemon 2>&1 | grep "already in use"` ]]; then echo "[RethinkDB] is (probably) already running"; fi

external/casperjs:
	@tools/casper_install.sh

test_backend: db celery
	rm -f *_test_*.yaml
	nosetests -v mltsp

test_frontend: external/casperjs db celery
	echo -e "testing:\n    disable_auth: 1\n    test_db: 1" > "mltsp-_test_.yaml"
	@PYTHONPATH="." tools/casper_tests.py

test_frontend_no_docker: external/casperjs db celery
	echo -e "testing:\n    disable_auth: 1\n    test_db: 1" > "mltsp-_test_.yaml"
	@PYTHONPATH="." NO_DOCKER=1 tools/casper_tests.py

test_entrypoint:
	mltsp --version

test: | test_entrypoint test_backend test_frontend

test_no_docker: | test_backend test_frontend_no_docker

install:
	pip install -r requirements.txt

html: celery
	pip install -q -r requirements.docs.txt
	notedown doc/examples/EEG_Example.md > doc/examples/EEG_Example.ipynb
	jupyter nbconvert --execute --inplace doc/examples/EEG_Example.ipynb --ExecutePreprocessor.timeout=300
	jupyter nbconvert --to=mdoutput --output=EEG_Example_output.md --output-dir=doc/examples doc/examples/EEG_Example.ipynb
	export SPHINXOPTS=-W; make -C doc html
	cp doc/examples/EEG_Example.ipynb doc/_build/html/examples/
