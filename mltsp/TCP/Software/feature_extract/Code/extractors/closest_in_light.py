from __future__ import print_function
from ..FeatureExtractor import ContextFeatureExtractor

class closest_in_light(ContextFeatureExtractor): 
        """distance_in_arcmin_to_nearest_galaxy"""
        active = True
        extname = 'closest_in_light' #extractor's name
        
        light_cutoff = 4.0 ## dont report anything farther away than this
        verbose = False
        def extract(self):
                n = self.fetch_extr('interng')
                
                try:
                        tmp = n["closest_in_light"]
                except:
                        return None # 20081010 dstarr adds try/except in case NED mysql cache server is down

                if tmp is None or tmp > self.light_cutoff:
                        rez = None
                else:
                        rez = tmp
                if self.verbose:
                        print(n)
                return rez
