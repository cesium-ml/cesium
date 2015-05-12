#!/bin/bash

echo "Drone systems check..."
echo "----------------------------------------------------"
echo "Current path:"
pwd
echo "Docker info:"
docker -H unix:///var/run/docker.sock info
echo "----------------------------------------------------"
