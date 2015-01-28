#/bin/env python

"""
makes some fake data for Maxime's codes
"""

import datetime
import os, sys
import numpy
import cPickle
__version__ = "v0.01"

class DataSet:
	
	def __init__(self,outname="tmp",clobber=True,odir="./"):
		self.dict     = None  # the dictionary representation
		self.xml      = None  # the XML representation of this data
		self.outname  = outname
		self.odir     = odir

		if outname == "time":
			## generate the outname from datetime
			outname = "data" + str(datetime.datetime.now()).replace(" ","")

		if clobber:
			if os.path.exists(odir + outname + ".pkl"):
				os.remove(odir + outname + ".pkl")
			if os.path.exists(odir + outname + ".xml"):
				os.remove(odir + outname + ".xml")		

	def make_dict(self):
		self.data = {"B": {"t": numpy.array([23455.12,23455.23,23455.56,23455.901,23456.102,23456.9,123457.8]),\
					       "f": numpy.array([12.02,   13.4,    12.00,   17.00,    12.01,    13.4,   13.56]), \
                           "rms": numpy.array([0.02,   0.78,    0.05,   0.10,     0.03,    0.89,    0.45]), \
                           "flux_units": "mag"},\
				     "V": {"t": numpy.array([23455.12,23455.23,23455.56,23455.901,23456.102,23456.9,123457.8]),\
						   "f": numpy.array([15.02,   16.5,    16.00,   19.00,    14.2,    17.6,   19.56]), \
				           "rms": numpy.array([0.02,   0.78,    0.05,   0.10,     -999,    0.89,    -99]), \
				           "flux_units": "mag"},\
					 "I": {"t": numpy.array([23455.12,23455.23,23455.56,23455.901,23456.102,23456.9,123457.8]),\
						   "f": numpy.array([15.02,   16.5,    17.00,   19.00,    19.2,    17.6,   11.56]), \
					       "rms": numpy.array([0.2,   3.4,      5.0 ,    -999,     1.0,     3.0,   -99.0]), \
					       "flux_units": "uJy"}}
				
		self.dict = {"id": self.outname, "version": __version__, "lower_limit_code": -99, "upper_limit_code": -999, 'data': self.data}
	
	def get_dict(self):
		if self.dict == None:
			self.make_dict()
		return self.dict
	
	def make_xml(self):
		## probably want to make the XML first then create the dictionary parse of it
		pass
	
	def pickle(self):
		output = open(self.odir + self.outname + ".pkl", 'wb')
		cPickle.dump(self.dict, output,-1)
		output.close()
		return self.odir + self.outname + ".pkl", 'wb'


