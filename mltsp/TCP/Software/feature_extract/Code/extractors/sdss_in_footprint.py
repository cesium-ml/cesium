from ..FeatureExtractor import ContextFeatureExtractor

class sdss_in_footprint(ContextFeatureExtractor): 
        """Is the source in the sdss footprint"""
        active = True
        extname = 'sdss_in_footprint' #extractor's name
        
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
                    return 0
                else:
                    return 1

