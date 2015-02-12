from __future__ import print_function
from ..FeatureExtractor import ContextInterExtractor
#from ..FeatureExtractor import FeatureExtractor
import math
rad2deg = 180.0/math.pi

ok_to_use = True
try:
	import ephem
except:
	print("!position_intermedite_extractor: pyephem not installed. The position features will fail.")
	ok_to_use = False

default = {'galb': None, 'gall': None, 'ecb': None, 'ecl': None, 'ra': None, 'dec': None}

class position_intermediate_extractor(ContextInterExtractor):
#class position_intermediate_extractor(FeatureExtractor):
	""" intermediate position extractor """
	active = True
	extname = 'position_intermediate'
	exttype = "context"
	
	if active and not ok_to_use:
		active = False
	
	def extract(self):
		if not self.active:
			return default
		
		ret = default
		## do some tests on the data
		try:
			if self.ra < 0.0 or self.ra >= 360.0:
				ret.update({'ra': None})
			else:
				ret.update({'ra': ephem.degrees(str(self.ra))})
		except:
				ret.update({'ra': None})

		try:
			if self.dec < -90.0 or self.dec > 90.0:
				ret.update({'dec': None})
			else:
				ret.update({'dec': ephem.degrees(str(self.dec))})
		except:
				ret.update({'dec': None})
		
		if ret['dec'] is not None and ret['ra'] is not None:
			np = ephem.Equatorial(ret['ra'],ret['dec'],epoch='2000')
		else:
			return ret
		g = ephem.Galactic(np)
		e = ephem.Ecliptic(np)

		ret = {'galb': rad2deg*float(g.lat), 'gall': rad2deg*float(g.long), \
				   'ecb':  rad2deg*float(e.lat), 'ecl':  rad2deg*float(e.long), \
				    'ra':  rad2deg*float(np.ra), 'dec':  rad2deg*float(np.dec)}

		return ret
