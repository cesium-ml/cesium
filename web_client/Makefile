.PHONY: all paths supervisord

SHELL=/bin/bash

# Supervisord only runs under Python 2, but that is no problem, even
# if everything else runs under Python 3.
SUPERVISORD=supervisord

all: supervisord

paths:
	mkdir -p log run
	mkdir -p log/sv_child

supervisord: paths
	$(SUPERVISORD) -c supervisord.conf

logs:
	rm -f log/*.log
	touch `cat supervisord.conf | grep "\.log" | cut -d '=' -f 2`
	tail -F log/*.log 2>/dev/null &

monitor: | logs supervisord
