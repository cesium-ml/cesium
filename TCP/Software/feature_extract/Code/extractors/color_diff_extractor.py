from ..FeatureExtractor import FeatureExtractor, InterExtractor

#class static_colors_extractor(FeatureExtractor): # Using this will add a 'X' feature in vosource xml whose value is a string representation of the returned od dict.  (using internal_use_only=False, active=False)
class static_colors_extractor(InterExtractor):
        """ Retrieve non timeseries colors (average, or single measurment)

        These colors are not intended to be used as features, but instead used
        in color difference features.

        Initially coded to use cdsclient NOMAD colors.
        
        """
	#active = False  # TODO probably want False
	internal_use_only = False # if set True, then seems to run all X code for each sub-feature
	active = True # if set False, then seems to run all X code for each sub-feature
	extname = 'static_colors' #extractor's name

	def extract(self):
            """ TODO: want to check if self.static_colors exists of len() != 0
                   - if not, then want to retrieve from NOMAD servers
               - Maybe these values will be inserted prior to feature generation by some code which has cached / inmemory access to NOMAD info for all TUTOR sources - in order to remove the need for netowrk or disk access.
            """
            #self.static_colors = {'B':15.900,
            #                      'V':15.600, # None
            #                      'R':15.370,
            #                      'J':15.617,
            #                      'H':15.496,
            #                      'K':14.641}

            self.static_band_names = ['B:NOMAD', 'V:NOMAD', 'R:NOMAD', 'J:NOMAD', 'H:NOMAD', 'K:NOMAD', 'extinct_bv']
            self.static_colors = {}
            for band in self.static_band_names:
                #self.static_colors[band] = self.properties['data'][band]['input']['flux_data'][0]
                self.static_colors[band] = self.properties['data'].get(band,{}) \
                                                                  .get('input',{}) \
                                                                  .get('flux_data',[None])[0]
            return self.static_colors


class color_diff_jh_extractor(FeatureExtractor):
	""" Generate color difference features using non timeseries, static or 
        average color magnitude measurements.  Initially coded to use
        cdsclient NOMAD colors.
	"""
	active = True
	extname = 'color_diff_jh' #extractor's name
        color_name1 = 'J:NOMAD'
        color_name2 = 'H:NOMAD'

	def extract(self):

            self.static_colors = self.properties['data'][self.band]['inter']['static_colors'].result

            color_1 = self.static_colors[self.color_name1]
            color_2 = self.static_colors[self.color_name2]
            
            if ((color_1 != -99) and (color_1 != None) and (color_2 != -99) and (color_2 != None)):
                return color_1 - color_2
            else:
                return None


class color_diff_hk_extractor(color_diff_jh_extractor):
    extname = 'color_diff_hk'
    color_name1 = 'H:NOMAD'
    color_name2 = 'K:NOMAD'
    
class color_diff_bj_extractor(color_diff_jh_extractor):
    """ See color_diff_jh_extractor docstring.
    B-J chosen since it combines a survey with 2mass (which we have J-H and H-K features)
    """
    extname = 'color_diff_bj'
    color_name1 = 'B:NOMAD'
    color_name2 = 'J:NOMAD'
    
class color_diff_vj_extractor(color_diff_jh_extractor):
    """ See color_diff_jh_extractor docstring.
    V-J chosen since it combines a survey with 2mass (which we have J-H and H-K features)
    """
    extname = 'color_diff_vj'
    color_name1 = 'V:NOMAD'
    color_name2 = 'J:NOMAD'

class color_diff_rj_extractor(color_diff_jh_extractor):
    """ See color_diff_jh_extractor docstring.
    R-J chosen since it combines a survey with 2mass (which we have J-H and H-K features)
    """
    extname = 'color_diff_rj'
    color_name1 = 'R:NOMAD'
    color_name2 = 'J:NOMAD'

class color_bv_extinction_extractor(FeatureExtractor):
	""" NED galactic extinction estimate from ned.ipac.caltech.edu given an ra,dec.
	This is the E(B-V) value from G. Schlegel et al.  1998ApJ..500..525S.
	This value is stored in TCP/Data/best_nomad_src_list for a srcid, along with NOMAD colors.
	"""
	active = True
	extname = 'color_bv_extinction' #extractor's name

	def extract(self):
            self.static_colors = self.properties['data'][self.band]['inter']['static_colors'].result

            return self.static_colors['extinct_bv']
