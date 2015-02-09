from ..FeatureExtractor import FeatureExtractor

class median_buffer_range_percentage_extractor(FeatureExtractor):
    """ extracts the percentage of points that fall within the buffer reang of 
    the median """
    active = True
    extname = 'median_buffer_range_percentage' #extractor's name
    def extract(self):
        magic_number = 1/10.0 #defines size of buffer range with respect to abs(max) - abs(min)
        max = self.fetch_extr('max')
        min = self.fetch_extr('min')
        median = self.fetch_extr('median')
        try:
            buffer_range = (abs(max) - abs(min))*(magic_number)
            points_within_buffer_range_of_median = 0
            for n in self.flux_data:
                if abs(n - median) < buffer_range:
                    points_within_buffer_range_of_median += 1
                else:
                    pass
            #print '!!!!', points_within_buffer_range_of_median/float(len(self.flux_data))
            return points_within_buffer_range_of_median/float(len(self.flux_data))
        except:
            return None