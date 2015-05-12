#!/bin/bash

echo "Drone systems check..."
echo "----------------------------------------------------"
ls -al /
echo "Docker info:"
docker -H unix:///docker.sock info
echo "----------------------------------------------------"
