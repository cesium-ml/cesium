#!/usr/bin/env python 
"""
Compile the python module using fortran code using:

f2py -c flaplace.f -m flaplace

"""
from __future__ import print_function
import os, sys
import numpy


class Simple_Fortran_Test:
    """
    Compile the python module using fortran code using:

    f2py -c flaplace.f -m flaplace

    """ 

    def fortranTimeStep(self, u, dx, dy):
        """Takes a time step using a simple fortran module that
        implements the loop in Fortran.  """
        u_new, err = flaplace.timestep(u, dx, dy)
        return u_new

    def func3(self, x,y):
        return (1- x/2 + x**5 + y**3)*numpy.exp(-x**2-y**2)

    def main(self):
        x, y = numpy.meshgrid(numpy.arange(-2,2,1), numpy.arange(-2,2,1))
        u = self.func3(x,y)
        dx = 1
        dy = 1
        for i in range(10):
            u = self.fortranTimeStep(u, dx, dy)
            print(u)
        
class RF_Fortran_Test:
    """ Wrapping PARF missing-value Fortran re-implementation of RandomForest.

    """

    def main(self):
        """
        """
        pass




if __name__ == '__main__':


    RFFortranTest = RF_Fortran_Test()
    RFFortranTest.main()
    

    ### For just testing that fortran module compiling works:
    if 1:
        import flaplace
        SimpleFortranTest = Simple_Fortran_Test()
        SimpleFortranTest.main()

        
