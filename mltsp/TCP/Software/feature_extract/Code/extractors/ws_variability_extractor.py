from __future__ import print_function
from ..FeatureExtractor import MultiFeatureExtractor
from ..FeatureExtractor import FeatureExtractor

from numpy import *

class ws_variability_self_extractor(FeatureExtractor):
	""" JSB adds this...a self variability for a single band
	http://articles.adsabs.harvard.edu/cgi-bin/nph-iarticle_query?db_key=AST&bibcode=1996PASP..108..851S&letter=0&classic=YES&defaultprint=YES&whole_paper=YES&page=852&epage=852&send=Send+PDF&filetype=.pdf 
	page 853, equation in top left of the page
	"""
	active = True
	extname = 'ws_variability_self' #extractor's name
	compared_extr = 'n_points'
	minpoints = 2  # 20081010: dstarr adds this variable, although it doesn't seem to used anywhere... # 20081108: changed min_points to minpoints, as expected by FeatureExtractor (this was a typo)
	maxpoints = 10000 #20090127: dstarr adds this after seeing a ws_variability_extractor related memory balloon possibly due to a +30k dataset.
	def extract(self):
		band1= self.band
		band2= self.band
		n1 = self.extr # n_points from band 1
		n2 = self.extr
		self.dic1 = self.dic # the dictionary in band 1
		self.dic2 = self.dic
		timeindices = indexb, indexv = self.find_close_points(self.dic['input']['time_data'] , self.dic['input']['time_data']) # find the indices of the points 
		meanb = self.fetch_extr('dc') # b bar JSB changed to dc instead of old_dc
		meanv = self.fetch_extr('dc')  # v bar
		bi = self.dic['input']['flux_data'][indexb]
		vi = self.dic['input']['flux_data'][indexv]
		sigbi = self.dic['input']['rms_data'][indexb]
		sigvi = self.dic['input']['rms_data'][indexv]
		insum = ((bi - meanb) / sigbi) * ( (vi - meanv) / sigvi)
		summed = insum.sum()
		n = float(len(indexb))
		try:
			I = sqrt(1 / (n * (n-1) ) ) * summed
			print("ws_variability_self for band %s = %f" % (self.band,I))
		except:
			# if p'time_data'] just contains multiple same times, then n==1 & Excepts.
			I = None 
		return I


	def find_close_points(self, times1, times2):
		""" find points in the two bands that were sampled close in time to each other """
		times1x, times2x = ix_(times1, times2) # http://www.scipy.org/Tentative_NumPy_Tutorial#head-05b0dc978ba9ce86c363b3fa92a6e4869e6c72a9
		# 20080702: dstarr noticies that we occasionally get a python MemoryError here.  Due to large timeseries datasets?  Is this an inefficeint algorithm?:
		timediff = abs(times1x - times2x) # the difference in time between any two points
		zeromatrix = zeros((len(times1),len(times2)) ) # a matrix full of zeros of the same dimensions as timediff
		min1 = timediff.argmin(axis=0) # find the index of the minimum down each column
		min2 = timediff.argmin(axis=1) # find the index of the minimum across each row
		minmatrix1 = zeromatrix
		minmatrix2 = zeromatrix.copy()
		minmatrix1[min1 , arange(len(times2))] = 1 # mark the column minima with 1
		minmatrix2[arange(len(times1)), min2] = 1 # mark the row minima with 1
		boolmatrix = logical_and(minmatrix1,minmatrix2) # intersection
		return where(boolmatrix) # the indices the of intersection points


class ws_variability_bv_extractor(MultiFeatureExtractor):
	""" http://articles.adsabs.harvard.edu/cgi-bin/nph-iarticle_query?db_key=AST&bibcode=1996PASP..108..851S&letter=0&classic=YES&defaultprint=YES&whole_paper=YES&page=852&epage=852&send=Send+PDF&filetype=.pdf 
	page 853, equation in top left of the page
	"""
	active = True
	extname = 'ws_variability_bv' #extractor's name
	band1 = 'b'
	band2 = 'v'
	compared_extr = 'n_points'
	def extract(self):
		n1 = self.extr1 # n_points from band 1
		n2 = self.extr2
		self.dic1 = self.dic1 # the dictionary in band 1
		self.dic2 = self.dic2
		timeindices = indexb, indexv = self.find_close_points(self.dic1['input']['time_data'] , self.dic2['input']['time_data']) # find the indices of the points 
		meanb = self.fetch_extr('dc', band=self.band1) # b bar JSB changed to dc instead of old_dc
		meanv = self.fetch_extr('dc', band=self.band2) # v bar
		bi = self.dic1['input']['flux_data'][indexb]
		vi = self.dic2['input']['flux_data'][indexv]
		sigbi = self.dic1['input']['rms_data'][indexb]
		sigvi = self.dic2['input']['rms_data'][indexv]
		insum = ((bi - meanb) / sigbi) * ( (vi - meanv) / sigvi)
		summed = insum.sum()
		n = float(len(indexb))
		I = sqrt(1 / (n * (n-1) ) ) * summed
		return I


	def find_close_points(self, times1, times2):
		""" find points in the two bands that were sampled close in time to each other """
		times1x, times2x = ix_(times1, times2) # http://www.scipy.org/Tentative_NumPy_Tutorial#head-05b0dc978ba9ce86c363b3fa92a6e4869e6c72a9
		timediff = abs(times1x - times2x) # the difference in time between any two points
		zeromatrix = zeros((len(times1),len(times2)) ) # a matrix full of zeros of the same dimensions as timediff
		min1 = timediff.argmin(axis=0) # find the index of the minimum down each column
		min2 = timediff.argmin(axis=1) # find the index of the minimum across each row
		minmatrix1 = zeromatrix
		minmatrix2 = zeromatrix.copy()
		minmatrix1[min1 , arange(len(times2))] = 1 # mark the column minima with 1
		minmatrix2[arange(len(times1)), min2] = 1 # mark the row minima with 1
		boolmatrix = logical_and(minmatrix1,minmatrix2) # intersection
		return where(boolmatrix) # the indices the of intersection points
		
class ws_variability_ru_extractor(ws_variability_bv_extractor):
	extname = 'ws_variability_ru'
	band1 = 'r'
	band2 = 'u'
	
class ws_variability_ug_extractor(ws_variability_bv_extractor):
    extname = 'ws_variability_ug'
    band1 = 'u'
    band2 = 'g'

class ws_variability_gr_extractor(ws_variability_bv_extractor):
    extname = 'ws_variability_gr'
    band1 = 'g'
    band2 = 'r'

class ws_variability_ri_extractor(ws_variability_bv_extractor):
    extname = 'ws_variability_ri'
    band1 = 'r'
    band2 = 'i'

class ws_variability_iz_extractor(ws_variability_bv_extractor):
    extname = 'ws_variability_iz'
    band1 = 'i'
    band2 = 'z'
    
