#!/bin/bash

for i in {0..6}
do
    mknod -m0660 /dev/loop$i b 7 $i
done
