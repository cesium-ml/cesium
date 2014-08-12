""" This module is an implementation of lomb_scargle using type( """

from ..FeatureExtractor import FeatureExtractor
from ..FeatureExtractor import InterExtractor
from common_functions.lomb_scargle import lomb
from common_functions.pre_whiten import pre_whiten

from pylab import *

class lomb_scargle_extractor(InterExtractor):
	""" wrapper for common_functions lomb_scargle and pre_whiten
	"""
	internal_use_only = False
	active = False
	extname = 'lomb_scargle' 
	def extract(self):
		x = self.time_data
		nx = len(x)
		dx = zeros(nx,dtype=float)
		y = self.flux_data
		dy = self.rms_data
		
		time = x
		time.sort
		dt = median( time[1:]-time[:-1] )
		maxlogx = log(0.5/dt) # max frequency is ~ the sampling rate
		minlogx = log(0.5/(time[-1]-time[0])) #min frequency is 0.5/T
		# sample the PSD with 1% fractional precision
		M=long(ceil( (maxlogx-minlogx)*100. ))
		frequencies = exp(maxlogx-arange(M, dtype=float) / (M-1.) * (maxlogx-minlogx))
		num_freq_comps = 3
		out_dict={}
		ytest=y
		dof = len(x)
		if (dof>=5):
		
			for i in range(num_freq_comps):
				psd, freqs, signi, sim_signi, peak_sort = lomb(x,ytest,delta_time=dx, signal_err=dy,freqin=frequencies,verbosity=0)
				imax = psd.argmax()
				freq_max = freqs[imax]
				ytest, harm_dict = pre_whiten(x, ytest, freq_max, delta_time=dx, signal_err=dy, dof=dof, nharm_min=4, nharm_max=100)
				dstr = "freq%i" % (i+1)
				out_dict['freq_searched_min']=min(freqs)
				out_dict['freq_searched_max']=max(freqs)
				out_dict[dstr] = freq_max
				out_dict[dstr+"_signif"] = signi
				#if (dof>0 and harm_dict['nharm']>0 and harm_dict['signif']>0):
				#        out_dict[dstr+"_harmonics"] = harm_dict
				#else:
				#        out_dict[dstr+"_harmonics"] = {}
				#dof = dof - harm_dict['nharm']*2.
				
				# 20080508: dstarr modifies harm_dict so it is a shallow dict which we can out_dict.update()
				if (dof>0 and harm_dict['nharm']>0 and harm_dict['signif']>0):
					for elem_k, elem_v in harm_dict.iteritems():
						out_dict[dstr + "_harmonics_" + elem_k] = elem_v
						# Do we even want to include this case as empty dict??? :
						#else:
						#       out_dict[dstr+"_harmonics"] = {}
						dof = dof - harm_dict['nharm']*2.
			#print out_dict.keys()
		return out_dict
		
class lomb_generic(FeatureExtractor):
	""" Generic lomb extractor grabs value from dictionary	"""
	internal_use_only = False
	active = True
	extname = 'to_be_overloaded' # identifier used in final extracted value dict.
	lomb_key = 'to_be_overloaded'
	def extract(self):
		lomb_dict = self.fetch_extr('lomb_scargle') # fetches the dictionary from lomb_scargle_extractor with the useful lomb scargle results in it
		# If lomb_dict is partially filled, most likely lomb couldn't compute completely due to FALSE condition: (dof>0 and harm_dict['nharm']>0 and harm_dict['signif']>0)
		if lomb_dict.has_key(self.lomb_key):
			return lomb_dict[self.lomb_key] # finds the correct keyword that this class is assigned to, this could be replaced by self.extname if it wasn't for the _alt
		else:
			self.exerror('Lomb Scargle Dictionary does not have key %s' % (self.lomb_key))
		
lomb_features = ['freq_searched_min', 'freq1_harmonics_rel_phase_error_1', 'freq1_harmonics_peak2peak_flux', 'freq1_harmonics_rel_phase_error_3', 'freq1_harmonics_rel_phase_error_2', 'freq1_harmonics_rel_phase_0', 'freq1_harmonics_rel_phase_1', 'freq1_harmonics_rel_phase_2', 'freq1_harmonics_rel_phase_3', 'freq1_harmonics_amplitude_2', 'freq1_harmonics_amplitude_3', 'freq1_harmonics_amplitude_0', 'freq1_harmonics_amplitude_1', 'freq2_signif', 'freq1_harmonics_peak2peak_flux_error', 'freq1_harmonics_signif', 'freq3', 'freq2', 'freq1', 'freq1_harmonics_rel_phase_error_0', 'freq1_harmonics_freq_0', 'freq1_harmonics_freq_1', 'freq1_harmonics_freq_2', 'freq1_harmonics_freq_3', 'freq3_signif', 'freq1_harmonics_nharm', 'freq1_harmonics_moments_err_0', 'freq1_harmonics_moments_err_1', 'freq1_harmonics_moments_err_2', 'freq1_harmonics_moments_err_3', 'freq1_signif', 'freq1_harmonics_moments_0', 'freq1_harmonics_moments_1', 'freq1_harmonics_moments_2', 'freq1_harmonics_moments_3', 'freq1_harmonics_amplitude_error_3', 'freq1_harmonics_amplitude_error_2', 'freq1_harmonics_amplitude_error_1', 'freq1_harmonics_amplitude_error_0', 'freq_searched_max']

for feature in lomb_features:
	print "About to prepare type", feature
	newclass = type(feature, (lomb_generic,), {'__doc__': feature, 'extname':feature, 'lomb_key':feature}) # see http://docs.python.org/lib/built-in-funcs.html for documentation of type()
	exec "%s = newclass" % (feature)
	print "new extname:"
	exec "print %s().extname" % (feature)








# regex from !'(\S+)',\n to 
#	class $1_extractor(lomb_generic):
#		""" $1 """
#		extname = "$1"
#		lomb_key = "$1"
#		
# (need a newline at the end)
