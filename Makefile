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
	nosetests -v cesium

install:
	pip install -r requirements.txt

doc_reqs:
	pip install -q -r requirements.docs.txt

MARKDOWNS = $(wildcard $(EXAMPLE_DIR)/*Example.md)
NOTEBOOKS = $(patsubst %Example.md, %Example.ipynb, $(MARKDOWNS))
MD_OUTPUTS = $(patsubst %.md, %_output.md, $(MARKDOWNS))

%Example.ipynb:%Example.md
	notedown $< > $@
	jupyter nbconvert --execute --inplace $@ --ExecutePreprocessor.timeout=-1

%_output.md:%.ipynb
	jupyter nbconvert --to=mdoutput --output=`basename $@` --output-dir=$(EXAMPLE_DIR) $<

html: | doc_reqs $(NOTEBOOKS) $(MD_OUTPUTS)
	export SPHINXOPTS=-W; make -C doc html
	cp $(EXAMPLE_DIR)/*.ipynb doc/_build/html/examples/
