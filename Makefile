.PHONY: all clean test

all:
	python setup.py build_ext -i

clean:
	find . -name "*.so" | xargs rm

webapp:
	tools/launch_waitress.py

init:
	python start_mltsp.py --db-init --force

db:
	@rethinkdb --daemon || echo "(RethinkDB probably already running)"

external/casperjs:
	tools/casper_install.sh

test_backend: db
	nosetests --exclude-dir=mltsp/Flask/src --nologcapture mltsp

test_frontend: external/casperjs
	tools/casper_tests.py

test: test_backend test_frontend

install:
	pip install -r requirements.txt
