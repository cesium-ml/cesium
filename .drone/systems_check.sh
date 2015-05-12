#!/bin/bash

echo "Drone systems check..."
echo "----------------------------------------------------"
ls -al /*.sock
ls -al /var/run/*.sock
echo "Docker info:"
docker -H unix:///docker.sock info
echo "----------------------------------------------------"
