#!/usr/bin/env python
"""
This script starts up a bunch of ipengines on nodes of the LCOGT cch1
beowulf cluster.

"""
import os, sys

if __name__ == '__main__':

    n_cpus_per_node = 8
    node_id_list = [1,2,3,4,5,6,7,8,9,10,0]

    for node_id in node_id_list:
        for i_cpu in xrange(n_cpus_per_node):
            exec_str = "bpsh %d ipengine >& /dev/null &" % (node_id)
            os.system(exec_str)
