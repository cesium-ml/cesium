.PHONY: all

all:
	python setup.py build_ext -i

clean:
	find . -name "*.so" | xargs rm
