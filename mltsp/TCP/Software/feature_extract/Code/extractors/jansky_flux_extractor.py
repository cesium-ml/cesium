from __future__ import print_function
from ..FeatureExtractor import InterExtractor
from numpy import *

class jansky_flux_extractor(InterExtractor):
	""" Convert the flux from magnitudes to janskies """
	active = True
	extname = 'jansky_flux' #extractor's name
	# def extract(self):
	# 	table1 = { \
	# 	"u": {"central":3650 ,  "width":680  ,   "f_lambda(0)": 4.27e-9 ,        "f_nu(0)": 1.90e-23,   "constant": 13.84}, \
	# 	"b": {"central":4400 ,  "width":980  ,   "f_lambda(0)": 6.61e-9 ,        "f_nu(0)": 4.27e-23,   "constant": 12.97}, \
	# 	"v": {"central":5500 ,  "width":890  ,   "f_lambda(0)": 3.64e-9 ,        "f_nu(0)": 3.67e-23,   "constant": 13.72}, \
	# 	"r": {"central":7000 ,  "width":2200 ,   "f_lambda(0)": 1.74e-9 ,        "f_nu(0)": 2.84e-23,   "constant": 13.54}, \
	# 	"i": {"central":9000 ,  "width":2400 ,   "f_lambda(0)": 8.32e-10,        "f_nu(0)": 2.25e-23,   "constant": 14.25}, \
	# 	"j": {"central":12500,  "width":3000 ,   "f_lambda(0)": 3.18e-10,        "f_nu(0)": 1.65e-23,   "constant": 15.05}, \
	# 	"h": {"central":16500,  "width":4000 ,   "f_lambda(0)": 1.18e-10,        "f_nu(0)": 1.07e-23,   "constant": 15.82}, \
	# 	"k": {"central":22000,  "width":6000 ,   "f_lambda(0)": 4.17e-11,        "f_nu(0)": 6.73e-24,   "constant": 16.50}, \
	# 	"l": {"central":36000,  "width":12000,   "f_lambda(0)": 6.23e-12,        "f_nu(0)": 2.69e-24,   "constant": 17.82}, \
	# 	} # table 1 from Misconceptions About Astronomical Magnitudes," E. Schulman and C. V. Cox, American Journal of Physics, Vol. 65, pg. 1003 (1997).
	# 	watts_m2 = self.fetch_extr('watt_per_m2_flux')
	# 	centerA = table1[self.band.lower()]['central'] # Angstrom
	# 	width = table1[self.band.lower()]['width'] # Angstrom
	# 	minA = centerA - width / 2
	# 	maxA = centerA + width / 2
	# 	minm = minA * 1e-10 # Angstrom to m
	# 	maxm = maxA * 1e-10
	# 	c = 299792458 # m / s
	# 	maxHz = c / minm
	# 	minHz = c / maxm
	# 	width_Hz = maxHz - minHz
	# 	jansky = watts_m2 / width_Hz # Jansky = W / m^2 / Hz
	# 	return jansky
	def extract(self):
		try:
			unit = self.flux_data_unit
		except NameError:
			unit = self.assumed_unit
		if unit in ['mag','mags','magnitude']:
			""" table from http://ssc.spitzer.caltech.edu/tools/magtojy/ref.html """
			zero_magnitude_fluxes = { \
			"u": 1823, \
			"b": 4130, \
			"v": 3781, \
			"r": 2941, \
			"i": 2635, \
			"j": 1603, \
			"h": 1075, \
			"k": 667 , \
			"l": 288 , \
			"m": 170 , \
			"n": 36  , \
			"o": 9.4 }
			try:
				""" This is inside a try/except to catch the possibility of the band not being in the zero_magnitude_fluxes dictionary """
				zero_magnitude = zero_magnitude_fluxes[self.band.lower()]
			except KeyError:
				self.ex_error("Band %s not found" % (self.band))
			""" follow the conversion method from http://ircamera.as.arizona.edu/astr_250/Lectures/Lec13_sml.htm """
			janskies = zero_magnitude * power(10, self.flux_data / (-2.5) )
			self.uncertainty = self.uncer_calc(janskies)
			return janskies
		else:
			print("units not recognized", self.flux_data_unit, self.extname)
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