from ..FeatureExtractor import InterExtractor
import numpy
from numpy import random
from scipy import fftpack, stats, optimize
from pylab import *
from common_functions import *

class watt_per_m2_flux_extractor(InterExtractor):
	""" Convert the magnitudes to SI units"""
	active = True
	extname = 'watt_per_m2_flux' #extractor's name
	def extract(self):
		#import pdb; pdb.set_trace()
		try:
			unit = self.flux_data_unit
		except NameError:
			unit = self.assumed_unit
		if unit in ['mag','mags','magnitude']:
			constants = 	\
			{"u": 13.84 	\
			,"b": 12.97 	\
			,"v": 13.72 	\
			,"r": 13.54 	\
			,"i": 14.25 	\
			,"j": 15.05 	\
			,"h": 15.82 	\
			,"k": 16.50 	\
			,"l": 17.82} # from Misconceptions About Astronomical Magnitudes," E. Schulman and C. V. Cox, American Journal of Physics, Vol. 65, pg. 1003 (1997). Table 1
			try:
				if 'clear' in self.band.lower():
					constant = constants['v'] # 20100722 kludge to get some debosscher data ingested
				else:
					# 20100518 dstarr adds a kludge which tries assuming that the first character of band string is a filter.  Realistically, we need to have constants{} entries for all 24 bands found in the lyra:tutor:filters (take first elem
					constant = constants[self.band[0].lower()] # find the right constant by enforcing lower case
			except KeyError:
				self.ex_error("Band %s not found" % (self.band))
			f = 10**(-0.4*(self.flux_data + constant)) # ergs per second per cm^2, equation 11 of the above-mentioned paper
			fwatt = f * 1e-7 # conversion from erg/s to watts
			fm2 = fwatt * 1e4 # 10 000 cm^2 in a m^2
			self.uncertainty = self.uncer_calc(fm2)
			return fm2
		else:
			print "units not recognized", self.flux_data_unit, self.extname
			self.uncertainty = self.rms_data
			return self.flux_data # else assume it's already in those units, no unit conversion implemented for the moment
	def uncer_calc(self, flux_wm2):
		""" calculate the uncertainty in the SI flux 
		Latex for the approximation (valid if the flux uncertainty is less than 10%):
		
		\sigma_m &=& \sqrt{  \sigma_{m,higher} \times \sigma_{m, lower}} \\
		&=& \sqrt{ \left( 2.5 \log_{10}(f - \sigma_f) - 2.5\log_{10}f \right) \times \left( -2.5 \log_{10}(f + \sigma_f) + 2.5\log_{10}f \right) } \\
		&=& \sqrt{ -2.5^2 \log_{10}\left(\frac{f}{f-\sigma_f}\right) \left(\log_{10}\frac{f}{f+\sigma_f}\right)}  \\
		&=& \sqrt{ -2.5^2 \log_{10}\left(\frac{f-\sigma_f}{f}\right) \log_{10}\left(\frac{f+\sigma_f}{f}\right)} \\
		&=& 2.5\sqrt{ -\log_{10}\left( 1 - \frac{\sigma_f}{f} \right) \log_{10}\left( 1 + \frac{\sigma_f}{f} \right)} \\
		&=&   \frac{2.5 }{\ln 10} \sqrt{ -\ln\left( 1 - \frac{\sigma_f}{f} \right) \ln\left( 1 + \frac{\sigma_f}{f} \right)} \\
		&\approx & \frac{2.5 }{\ln 10} \sqrt{ \left(\frac{\sigma_f}{f} \right) ^2 } \\
		&\approx & \frac{\sigma_f}{f}
		
		"""
		f = flux_wm2
		sigmam = self.rms_data
		sigmaf = f * sigmam
		return sigmaf
