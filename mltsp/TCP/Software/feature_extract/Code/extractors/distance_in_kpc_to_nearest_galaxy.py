from __future__ import print_function
from __future__ import absolute_import
from ..FeatureExtractor import ContextFeatureExtractor

from . import ned

class distance_in_kpc_to_nearest_galaxy(ContextFeatureExtractor): 
	"""distance_in_kpc_to_nearest_galaxy"""
	active = True
	extname = 'distance_in_kpc_to_nearest_galaxy' #extractor's name
	
	cutoff = 1000.0 ## kpc
	verbose = False
	def extract(self):
		n = self.fetch_extr('tmpned')

		#if not isinstance(n,ned.NED):
		#	self.ex_error("bad ned instance")

		try:
			tmp = n.distance_in_kpc_to_nearest_galaxy()
		except:
			return None # 20081010 dstarr adds try/except in case NED mysql cache server is down
		if tmp['distance'] is None or tmp['distance'] > self.cutoff:
			## JSB change to None because we assume we dont have a result here
			rez = None
		else:
			rez = tmp['distance']
		if self.verbose:
			print(tmp)
		return rez

