#!/bin/bash

echo "Drone systems check..."
echo "----------------------------------------------------"
echo "Current path:"
pwd
echo "Docker info:"
docker -H unix:///var/run/docker.sock info
echo "Drone shared temp:"
ls -al /tmp/
ls -al /tmp/drone_shared
cat /tmp/drone_shared/*.txt
echo "----------------------------------------------------"
