.PHONY: all clean test

all:
	python setup.py build_ext -i

clean:
	find . -name "*.so" | xargs rm

test:
	nosetests --exclude-dir=mltsp/Flask/src --nologcapture

