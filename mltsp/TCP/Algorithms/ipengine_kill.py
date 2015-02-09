#!/usr/bin/env python 
""" This kills ipython-parallel's ipengine which I cannot
seem to directly ssh-exeucte a pkill on.
"""
import sys, os

if __name__ == '__main__':

    command_str = "ps awwux | grep bin.ipengine" 

    (a,b,c) = os.popen3(command_str)
    a.close()
    c.close()
    lines = b.readlines()
    b.close()

    for line in lines:
        if len(line)  >10:
            line_list = line.split()
            try:
                pid = int(line_list[1])
                exec_str = "kill -9 %d" % (pid)
                os.system(exec_str)
            except:
                pass
