try:
	from ..FeatureExtractor import FeatureExtractor
except:
	import os
	ppath = os.environ.get('PYTHONPATH')
	os.environ.update({'PYTHONPATH': ppath + ":" + os.path.realpath("..")})
	#print os.environ.get("PYTHONPATH")
	from FeatureExtractor import FeatureExtractor 

import unittest
import sys
from scipy import stats
import numpy

class amplitude_extractor(FeatureExtractor):
	""" Returns the half the difference between the maximum magnitude and the minimum magnitude.
	Note this will also work for data that is given in terms of flux. So in a sense, it's
	a volitile feature across different datasets.
	
	Suggestion: use the new percent_amplitude below instead. Turn this one off?
	
	"""
	active = True
	extname = 'amplitude' #extractor's name
	def extract(self):
		maxm = self.fetch_extr('max') # maximum magnitude
		minm = self.fetch_extr('min') # minimum magnitude
		try:
			amplitude = maxm - minm
		except:
			return None
		#print ("absolute",amplitude)
		
		return amplitude/2.0

class percent_amplitude_extractor(FeatureExtractor):
		""" Returns the largest percentage difference between the maximum 
		magnitude and the minimum magnitude relative to the median.
		
		assumes that the flux data is in units of magnitudes unless flux_data_unit has been set otherwise.
		"""
		active = True
		extname = 'percent_amplitude' #extractor's name
		assumed_unit = "mag" # 20100518: actually, I think a unitless percentage is returned.
		def extract(self):
			maxm = self.fetch_extr('max') # maximum magnitude
			minm = self.fetch_extr('min') # minimum magnitude
			medd = self.fetch_extr("median")
			try:
				unit = self.flux_data_unit
			except NameError:
				unit = self.assumed_unit
			
			try:
				if unit in ['mag','mags','magnitude']:
					maxm = 10**(-0.4*maxm)
					minm = 10**(-0.4*minm)
					medd = 10**(-0.4*medd)
				
				amplitude = maxm - minm
				#20100916dstarr comments this out since the different numerators seems not very useful/consistant:
				#tmp = [(maxm - medd)/medd, medd/(maxm - medd), (minm - medd)/medd, medd/(minm - medd)]
				#20100916dstarr adds this instead:
				tmp = [abs((maxm - medd)/medd), abs((minm - medd)/medd)]
				#print ("percent",max(tmp))
				return max(tmp)
			except:
				return None


class percent_difference_flux_percentile_extractor(FeatureExtractor):
		""" The 2nd & 98th flux percentiles are subtracted and converted into magnitude.
		Assumes that the flux data is in units of magnitudes unless flux_data_unit has been set otherwise.
		This algorithms is mentioned by Eyer (2005) arXiv:astro-ph/0511458v1
		and he references Evans & Belokurov (2005).

		I actually use 5th and 95th since we could be interested in sources with less than 50-100 epochs.

		"""
		active = True
		extname = 'percent_difference_flux_percentile' #extractor's name
		assumed_unit = "mag" # 20100518: actually, I think a unitless percentage is returned.
		def extract(self):
			watts_m2 = self.fetch_extr('watt_per_m2_flux')
			try:
				flux_high = stats.scoreatpercentile(watts_m2, 95)
				flux_low = stats.scoreatpercentile(watts_m2, 5)
				flux_50 = stats.scoreatpercentile(watts_m2, 50)
				return (flux_high - flux_low) / flux_50
			except:
				return None


class flux_percentile_ratio_mid20_extractor(FeatureExtractor):
		"""
		mid20: A ratio of (60 flux percentile - 40 flux percentile) /
		                   (95 flux percentile - 5 flux percentile)
		"""
		active = True
		extname = 'flux_percentile_ratio_mid20' #extractor's name
		assumed_unit = "mag" # 20100518: actually, I think a unitless percentage is returned.
		def extract(self):
			watts_m2 = self.fetch_extr('watt_per_m2_flux')
			try:
				flux_high = stats.scoreatpercentile(watts_m2, 60)
				flux_low = stats.scoreatpercentile(watts_m2, 40)
				flux_diff_ref = stats.scoreatpercentile(watts_m2, 95) - \
						stats.scoreatpercentile(watts_m2, 5)
				return (flux_high - flux_low) / flux_diff_ref
			except:
				return None


class flux_percentile_ratio_mid35_extractor(FeatureExtractor):
		"""
		mid35: A ratio of (67.5 flux percentile - 32.5 flux percentile) /
		                   (95 flux percentile - 5 flux percentile)
		"""
		active = True
		extname = 'flux_percentile_ratio_mid35' #extractor's name
		assumed_unit = "mag" # 20100518: actually, I think a unitless percentage is returned.
		def extract(self):
			watts_m2 = self.fetch_extr('watt_per_m2_flux')
			try:
				flux_high = stats.scoreatpercentile(watts_m2, 67.5)
				flux_low = stats.scoreatpercentile(watts_m2, 32.5)
				flux_diff_ref = stats.scoreatpercentile(watts_m2, 95) - \
						stats.scoreatpercentile(watts_m2, 5)
				return (flux_high - flux_low) / flux_diff_ref
			except:
				return None


class flux_percentile_ratio_mid50_extractor(FeatureExtractor):
		"""
		mid50: A ratio of (75 flux percentile - 25 flux percentile) /
		                   (95 flux percentile - 5 flux percentile)
		"""
		active = True
		extname = 'flux_percentile_ratio_mid50' #extractor's name
		assumed_unit = "mag" # 20100518: actually, I think a unitless percentage is returned.
		def extract(self):
			watts_m2 = self.fetch_extr('watt_per_m2_flux')
			try:
				flux_high = stats.scoreatpercentile(watts_m2, 75)
				flux_low = stats.scoreatpercentile(watts_m2, 25)
				flux_diff_ref = stats.scoreatpercentile(watts_m2, 95) - \
						stats.scoreatpercentile(watts_m2, 5)
				return (flux_high - flux_low) / flux_diff_ref
			except:
				return None


class flux_percentile_ratio_mid65_extractor(FeatureExtractor):
		"""
		mid65: A ratio of (82.5 flux percentile - 17.5 flux percentile) /
		                   (95 flux percentile - 5 flux percentile)
		"""
		active = True
		extname = 'flux_percentile_ratio_mid65' #extractor's name
		assumed_unit = "mag" # 20100518: actually, I think a unitless percentage is returned.
		def extract(self):
			watts_m2 = self.fetch_extr('watt_per_m2_flux')
			try:
				flux_high = stats.scoreatpercentile(watts_m2, 82.5)
				flux_low = stats.scoreatpercentile(watts_m2, 17.5)
				flux_diff_ref = stats.scoreatpercentile(watts_m2, 95) - \
						stats.scoreatpercentile(watts_m2, 5)
				return (flux_high - flux_low) / flux_diff_ref
			except:
				return None

class flux_percentile_ratio_mid80_extractor(FeatureExtractor):
		"""
		mid80: A ratio of (90 flux percentile - 10 flux percentile) /
		                   (95 flux percentile - 5 flux percentile)
		"""
		active = True
		extname = 'flux_percentile_ratio_mid80' #extractor's name
		assumed_unit = "mag" # 20100518: actually, I think a unitless percentage is returned.
		def extract(self):
			watts_m2 = self.fetch_extr('watt_per_m2_flux')
			try:
				flux_high = stats.scoreatpercentile(watts_m2, 90)
				flux_low = stats.scoreatpercentile(watts_m2, 10)
				flux_diff_ref = stats.scoreatpercentile(watts_m2, 95) - \
						stats.scoreatpercentile(watts_m2, 5)
				return (flux_high - flux_low) / flux_diff_ref
			except:
				return None


class TestSequenceFunctions(unittest.TestCase):

	def setUp(self):
		self.seq = range(10)
	
	
if __name__ == '__main__':
	unittest.main()
