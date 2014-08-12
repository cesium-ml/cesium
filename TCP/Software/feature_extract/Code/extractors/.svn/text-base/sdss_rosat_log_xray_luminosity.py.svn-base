from ..FeatureExtractor import ContextFeatureExtractor

class sdss_rosat_log_xray_luminosity(ContextFeatureExtractor): 
        """What is the luminosity of the rosat source?"""
        active = True
        extname = 'sdss_rosat_log_xray_luminosity' #extractor's name
        light_cutoff = 0.2 ## dont report anything farther away than this in arcmin
        
        verbose = False
        def extract(self):
                n = self.fetch_extr('intersdss')
                
                if n is None:
                    if self.verbose:
                        print "Nothing in the sdss extractor"
                    return None
                    
                if not n.has_key("in_footprint"):
                    if self.verbose:
                        print "No footprint info in the sdss extractor. Should never happen."
                    return None
                
                if not n['in_footprint']:
                    if self.verbose:
                        print "Not in the footprint"
                    return None

                if not n.has_key("rosat_log_xray_luminosity"):
                    if self.verbose:
                        print "Desired parameter was not determined"
                    return None

                if not n.has_key("dist_in_arcmin"):
                    if self.verbose:
                        print "Desired parameter was not determined"
                    return None
                    
                if n["dist_in_arcmin"] > self.light_cutoff:
                    return None
                else:
                    rez = n["rosat_log_xray_luminosity"]
                if self.verbose:
                        print n
                return rez