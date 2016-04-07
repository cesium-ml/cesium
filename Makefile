.PHONY: all clean test

SHELL = /bin/bash
PY_VER = $(shell python -c 'import sys; print(sys.version_info.major)')
CLEAN_TEST_CONFIG = $(shell rm -f cesium-_test_.yaml)
EXAMPLE_DIR = doc/examples

celery:
	@if [[ -z `ps ax | grep -v grep | grep -v make | grep celery_tasks` ]]; then \
		PYTHONPATH="./cesium" celery worker -A celery_tasks -l info & \
	else \
		echo "[Celery] is already running"; \
	fi

.DEFAULT_GOAL := all

all:
	python setup.py build_ext -i

clean:
	find . -name "*.so" | xargs rm -f

webapp: db celery
	@rm -f cesium-_test_.yaml
	PYTHONPATH=. $(MAKE) -C web_client

init: db celery
	cesium --db-init --force

db:
	@if [[ -n `rethinkdb --daemon 2>&1 | grep "already in use"` ]]; then echo "[RethinkDB] is (probably) already running"; fi

external/casperjs:
	@tools/casper_install.sh

test_backend: db celery
	rm -f *_test_*.yaml
	nosetests -v cesium

test_frontend: external/casperjs db celery
	echo -e "testing:\n    disable_auth: 1\n    test_db: 1" > "cesium-_test_.yaml"
	@PYTHONPATH="." tools/casper_tests.py

test_frontend_no_docker: external/casperjs db celery
	echo -e "testing:\n    disable_auth: 1\n    test_db: 1" > "cesium-_test_.yaml"
	@PYTHONPATH="." NO_DOCKER=1 tools/casper_tests.py

test_entrypoint:
	cesium --version

test: | test_entrypoint test_backend test_frontend

test_no_docker: | test_backend test_frontend_no_docker

install:
	pip install -r requirements.txt

MARKDOWNS = $(wildcard $(EXAMPLE_DIR)/*Example.md)
NOTEBOOKS = $(patsubst %Example.md, %Example.ipynb, $(MARKDOWNS))
MD_OUTPUTS = $(patsubst %.md, %_output.md, $(MARKDOWNS))

%Example.ipynb:%Example.md
	notedown $< > $@
	jupyter nbconvert --execute --inplace $@ --ExecutePreprocessor.timeout=-1

%_output.md:%.ipynb
	jupyter nbconvert --to=mdoutput --output=`basename $@` --output-dir=$(EXAMPLE_DIR) $<

html: | celery $(NOTEBOOKS) $(MD_OUTPUTS)
	pip install -q -r requirements.docs.txt
	export SPHINXOPTS=-W; make -C doc html
	cp $(EXAMPLE_DIR)/*.ipynb doc/_build/html/examples/
