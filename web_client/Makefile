.PHONY: all paths supervisord

SHELL=/bin/bash

# Supervisord only runs under Python 2, but that is no problem, even
# if everything else runs under Python 3.
SUPERVISORD=supervisord

all: supervisord

paths:
	mkdir -p log run
	mkdir -p log/sv_child
	mkdir -p ~/.local/cesium/logs

supervisord: paths
	$(SUPERVISORD) -c supervisord.conf

logs: paths
	touch `cat supervisord.conf | grep "\.log" | cut -d '=' -f 2`
	touch log/{error,nginx-access,nginx-error}.log
	tail -F log/*.log 2>/dev/null &
	echo ~
	touch ~/.local/cesium/logs/errors_and_warnings.log
	tail -F ~/.local/cesium/logs/* 2>/dev/null &
	tail -F /var/log/nginx/error.log 2>/dev/null &

monitor: | logs supervisord
