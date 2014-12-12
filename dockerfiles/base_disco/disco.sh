#!/bin/sh
exec /sbin/setuser disco /disco/bin/disco nodaemon >>/var/log/disco.log 2>&1
