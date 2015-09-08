#!/bin/sh
exec /sbin/setuser rabbitmq /usr/sbin/rabbitmq-server >>/var/log/rabbitmq.log 2>&1
