.PHONY: all clean test

SHELL = /bin/bash
PY_VER = $(shell python -c 'import sys; print(sys.version_info.major)')
DISCO = $(DISCO_HOME)/bin/disco

py2:
	@if [[ $(PY_VER) != 2 ]]; then \
		echo -e "\n** Error: currently, MLTSP relies on Python 2.x **\n"; \
		exit 1; \
	fi

disco: py2
	@if [[ -z '$(DISCO_HOME)' ]]; then \
		echo -e "\n** Error: DISCO_HOME is not set. **\n"; \
		echo -e "Please follow the installation instructions in README.txt\n"; \
		exit 1; \
	else \
		if [[ -z `$(DISCO) status | grep running` ]]; then \
			$(DISCO) start ; \
		else \
		    echo "Disco is already running"; \
		fi; \
	fi

all: py2
	python setup.py build_ext -i

clean:
	find . -name "*.so" | xargs rm

webapp: py2 disco
	tools/launch_waitress.py

init: py2
	python start_mltsp.py --db-init --force

db:
	@rethinkdb --daemon || echo "(RethinkDB probably already running)"

external/casperjs: py2
	tools/casper_install.sh

test_backend: db py2 disco
	nosetests --exclude-dir=mltsp/Flask/src --nologcapture mltsp

test_frontend: external/casperjs py2 disco
	PYTHONPATH="." tools/casper_tests.py

test: test_backend test_frontend

install: py2
	pip install -r requirements.txt
