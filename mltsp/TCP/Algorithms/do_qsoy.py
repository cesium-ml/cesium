#!/usr/bin/env python
""" Nat wrote 20100930, dstarr to adapt as a TCP feature.
"""
from numpy import median,loadtxt
from qso_fit import qso_fit
import glob

if __name__ == '__main__':

    #files=glob.glob('*.dat')
    files=['/home/pteluser/scratch/100149386.dat']
    for file in files:
        id = file[file.rfind('/'):]
        (x,y,dy) = loadtxt(file,unpack=True)

        y0 = 19.
        y -= median(y) - y0
        od = qso_fit(x,y,dy,filter='g')
        res = od['chi2_qso/nu'],od['chi2_qso/nu_NULL']

        # QSO-like:  res[0]<~2
        # non-QSO: res[1]/res[0]<~2

        print ("%s %f %f") % (id,res[0],res[1]/res[0])
        import pprint
        pprint.pprint(od)
