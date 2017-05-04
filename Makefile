.PHONY: all clean test

SHELL = /bin/bash
PY_VER = $(shell python -c 'import sys; print(sys.version_info.major)')
EXAMPLE_DIR = doc/examples

.DEFAULT_GOAL := all

all:
	python setup.py build_ext -i

clean:
	find . -name "*.so" | xargs rm -f

test:
	python -m pytest -v

install:
	pip install -r requirements.txt

doc_reqs:
	pip install -q -r requirements.docs.txt

html: | doc_reqs
	export SPHINXOPTS=-W; make -C doc html
