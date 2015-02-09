from __future__ import absolute_import
from ..FeatureExtractor import FeatureExtractor
from .common_functions import ChiSquare

class chi2extractor(FeatureExtractor,ChiSquare):
	active = True
	extname = 'chi2' #extractor's name
	def extract(self):
		dc = self.fetch_extr('dc')
		chisquare = self.chi_square_sum(self.flux_data,lambda x: dc,x=self.time_data,rms=self.rms_data)
		return chisquare