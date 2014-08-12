from ..FeatureExtractor import InterExtractor
from common_functions import lomb_scargle
from common_functions.plot_methods import plot_vs_frequencies
from numpy import arange

class lomb_extractor(plot_vs_frequencies,InterExtractor):
	"""extracts a lomb scargle periodogram from the data"""
	active = True
	extname = 'lomb' #extractor's name
	minpoints = 5 # minimum number of points for the extractor to run
	def extract(self):
		""" NOTE: lightcurve.py:L228 actually calls lomb_scargle.lomb() and generates the psd and final L.S. freqs which are used as features.
		"""
		self.test_uneven()
		#noisedata = normal(loc=0,scale=5,size=int(round(freq*time)))
		#noisetime = self.time_data
		#noisedata = self.flux_data
		var = { 'x': self.time_data, 'y': self.flux_data, 'ylabel': 'Amplitude', 
	'xlabel':'Time (s)' }
		#N= len(noisetime)
		#dt = 1.0 #findAverageSampleTime(var,0)
		#maxlogx = log(1/(2*dt)) # max frequency is the sampling rate
		#minlogx = log(1/(max(var['x'])-min(var['x']))) #min frequency is 1/T
		#frequencies = self.frequencies#exp(arange(N, dtype = float) / (N-1.) * (maxlogx-minlogx)+minlogx)
		psd, freqs, signi, simsigni, psdpeaks = lomb_scargle.lomb(var['x'], 
	var['y'],freqin=self.frequencies,verbosity=0)
		#20071206 dstarr comment out:
		#result = psd
		#import pdb; pdb.set_trace()
		if 0:
		        ### TEST / DEBUGGING only:
			from common_functions import plot_analysis_psd
			plot_analysis_psd.do_plot(psd, freqs, signi, simsigni, psdpeaks, x=var['x'], y=var['y'])
			
		result = psd
		return result
	def test_uneven(self):
		uneven = False
		for x in arange(len(self.time_data)-3): 
			slicex = self.time_data[x:x+3] # slice with three elements
			if round((slicex[2] - slicex[1]),2) != round((slicex[1] - slicex[0]),2):
				uneven = True
				break
		if not uneven:
			self.ex_error("Evenly Spaced Data (don't waste my time!)")
			


				
