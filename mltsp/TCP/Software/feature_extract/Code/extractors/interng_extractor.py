from __future__ import absolute_import
from ..FeatureExtractor import ContextInterExtractor

#from power_extractor import power_extractor as power_extractor
from . import ng

class interng_extractor(ContextInterExtractor): 
    """intermediate call to the ng 200 Mpc galaxy server
    should get something like
    {'closest_in_light': 0.17192566500632125,
     'closest_in_light_absolute_bmag': -22.190000000000005,
     'closest_in_light_angle_from_major_axis': -125.26712677240506,
     'closest_in_light_dm': 33.200000000000003,
     'closest_in_light_physical_offset_in_kpc': 7.9431382807271822,
     'closest_in_light_position': (154.2234, 73.400639999999996),
     'closest_in_light_semimajor_r25_arcsec': 244.42816668246769,
     'closest_in_light_semiminor_r25_arcsec': 208.04211027151902,
     'closest_in_light_ttype': 3.8999999999999999,
     'closest_in_lightangular_offset_in_arcmin': 0.62555572920077607,
     'closest_units': 'galaxy_surface_brightness'}

    Explanation:
    closest_in_light = "the nearest galaxy, in units of that galaxies r25 surface brightness ellipse". Less than ~1.5 should indicate that the source is reasonably sure of being physically associated with that galaxy

    closest_in_light_absolute_bmag: extinction corrected absolute magnitude of the nearest galaxy

    closest_in_light_angle_from_major_axis: offset angle from the semi-major axis (I'd think that cc would be +-20 deg around 0 deg and 180 deg.

    closest_in_light_dm: best distance modulus known

    closest_in_light_ttype: galaxy t-type if reasonable certain otherwise None
    """
    active = True
    extname = 'interng' #extractor's name

    n = None
    def extract(self):
        posdict = self.fetch_extr('position_intermediate')

        if 'ra' not in posdict or posdict['dec'] is None:
            self.ex_error("bad RA or DEC in the intermediate ng extractor. check install pyephem and input coordinates")

        if not self.n:
            self.n = ng.get_closest_by_light(pos=(posdict['ra'],posdict['dec']))

        return self.n
