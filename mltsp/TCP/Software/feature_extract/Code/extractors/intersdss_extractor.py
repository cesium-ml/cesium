from __future__ import absolute_import
from ..FeatureExtractor import ContextInterExtractor

#from power_extractor import power_extractor as power_extractor
from . import sdss

class intersdss_extractor(ContextInterExtractor): 
	"""intermediate call to the sdss server
	{'best_dl': 4455.1248913899999,
	 'best_dm': 43.244299416029733,
	 'best_offset_in_kpc': 7.0559739096982508,
	 'bestz': 0.72108298999999998,
	 'dec': 0.79265430000000003,
	 'dered_g': 19.441016999999999,
	 'dered_i': 19.391967999999999,
	 'dered_r': 19.373417,
	 'dered_u': 19.644580999999999,
	 'dered_z': 19.353552000000001,
	 'dist_in_arcmin': 0.016127780000000001,
	 'in_footprint': True,
	 'objid': 587731513946275936L,
	 'photo2_flag': None,
	 'photo2_z_cc': None,
	 'photo2_z_d1': None,
	 'photo2_zerr_cc': None,
	 'photo2_zerr_d1': None,
	 'photo_z': None,
	 'photo_zerr': None,
	 'ra': 15.008567559999999,
	 'spec_confidence': 0.58286400000000005,
	 'spec_veldisp': None,
	 'spec_z': 0.72108300000000003,
	 'spec_zStatus': 'xcorr_loc',
	 'type': 'qso',
	 'url': 'http://cas.sdss.org/astrodr7/en/tools/explore/obj.asp?id=587731513946275936',
	 'urlalt': 'http://cas.sdss.org/astrodr7/en/tools/chart/navi.asp?ra=15.008568&dec=0.792654'}

	"""
	active = True
	extname = 'intersdss' #extractor's name
	verbose = True
	n = None
	light_cutoff = 0.2 ## dont report anything farther away than this in arcmin
    
	def extract(self):
		posdict = self.fetch_extr('position_intermediate')

		if 'ra' not in posdict or posdict['dec'] is None:
			self.ex_error("bad RA or DEC in the intermediate ng extractor. check install pyephem and input coordinates")

		#20090126 dstarr comments this conditional out: #if not self.n:
		if 'sdss_internal_struct' in self.properties['data']['multiband']['inter']:
			self.s = self.properties['data']['multiband']['inter']['sdss_internal_struct']
		else:
			self.s = sdss.sdssq(pos=(posdict['ra'],posdict['dec']),verbose=self.verbose,maxd=self.light_cutoff*1.05)
			
		return self.s.feature
