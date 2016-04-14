.PHONY: all clean test paths supervisord

# Supervisord only runs under Python 2, but that is no problem, even
# if everything else runs under Python 3.
SUPERVISORD=supervisord

SHELL = /bin/bash
.DEFAULT_GOAL := supervisord

celery:
	@if [[ -z `ps ax | grep -v grep | grep -v make | grep celery_tasks` ]]; then \
		PYTHONPATH="./cesium" celery worker -A cesium.celery_tasks -l info & \
	else \
		echo "[Celery] is already running"; \
	fi

clean:
	find . -name "*.so" | xargs rm -f

test: celery
	rm -f *_test_*.yaml
	nosetests -v cesium
install:
	pip install -r requirements.txt

paths:
	mkdir -p log run tmp
	mkdir -p log/sv_child
	mkdir -p ~/.local/cesium/logs

log: paths
	./tools/watch_logs.py

supervisord: paths
	$(SUPERVISORD) -c supervisord.conf
