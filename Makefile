.PHONY: all clean test

all:
	python setup.py build_ext -i

clean:
	find . -name "*.so" | xargs rm

test:
	PYTHONPATH=. python mltsp/TCP/tests/test_feature_generation.py

