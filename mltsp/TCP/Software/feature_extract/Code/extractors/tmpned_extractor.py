from __future__ import print_function
from __future__ import absolute_import
#from ..FeatureExtractor import FeatureExtractor
from ..FeatureExtractor import ContextInterExtractor
#from ..FeatureExtractor import MultiExtractor

#from power_extractor import power_extractor as power_extractor
from . import ned

class tmpned_extractor(ContextInterExtractor): 
	"""the Galactic coordinate b (latitude) in degrees"""
	active = True
	extname = 'tmpned' #extractor's name
	
	n = None
	def extract(self):
		#20080617_dstarr_comments_out#self.ex_error("let's not do this today")
		posdict = self.fetch_extr('position_intermediate')

		if 'ra' not in posdict or posdict['dec'] is None:
			self.ex_error("bad RA or DEC in the intermediate extractor. check install pyephem and input coordinates")
		
		if not self.n:
			#sys.path.append(os.path.abspath(os.environ.get("../../"))
			# This module should exist in the local path:
			#try: ### 20090123 dstarr comments this out.
			try:
				from . import ned_cache_server
				ncc = ned_cache_server.Ned_Cache_Client(ned_cache_server.pars)
				#self.n = ncc.retrieve_queue_ned_dict(posdict['ra'], \
				#			     posdict['dec'])
				(ned_obj, sdss_obj) = ncc.retrieve_queue_ned_dict(posdict['ra'], \
							     posdict['dec'])
				self.n = ned_obj
				#self.s = sdss_obj  # 20090126: I added this line a couple days ago, but I don't think it is useful/accessed.  So, I add the following line instead:
				self.properties['data']['multiband']['inter']['sdss_internal_struct'] = sdss_obj
				
			except:
				print("MySQL connection to NED cache server FAILED")
			###self.n = ned.NED(pos=(posdict['ra'],posdict['dec']),verbose=True, do_threaded=True) # dstarr changes flags to be verbose, ...
		
		
		return self.n #{'distance_in_kpc_to_nearest_galaxy': self.n.distance_in_kpc_to_nearest_galaxy(),\
			#'distance_in_arcmin_to_nearest_galaxy': self.n.distance_in_arcmin_to_nearest_galaxy()}

