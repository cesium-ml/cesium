from ..FeatureExtractor import FeatureExtractor

import scipy.optimize as optim
import numpy

class ar_is_theta_extractor(FeatureExtractor):
    '''
    AR-IS(1) model of Erdogan et al. (2005)
    http://www.siam.org/proceedings/datamining/2005/dm05_74erdogane.pdf

    This model should be fit on the *** Lomb-Scargle model subtracted data ***

    Model: x(t + delta) = theta^delta * x(t) + sigma_delta * eps
    eps ~ N(0,1)
    '''
    active = True
    extname = 'ar_is_theta'
    

    def sum_of_sq(self, theta,delta,x):
        return numpy.sum((x[1:] - theta**delta * x[:-1])**2)

    def extract(self):
        try:
            t = self.time_data
            m = self.flux_data
            n = len(t)
            
            # get the LS model residuals (for principal frequency)
            lomb_dict = self.fetch_extr('lomb_scargle')
            model = lomb_dict.get('freq1_model',[])
            x = m - model

            delta = t[1:] - t[:-1]

            # estimate theta
            theta = optim.fminbound(self.sum_of_sq, x1=0., x2=1., args=(delta, x))
            
            return theta
        except:
            return 0.0




class ar_is_sigma_extractor(FeatureExtractor):
    ''' returns the ratio of phase_dispersion-estimated and lomb_scargle-estimated frequencies '''
    active = True
    extname = 'ar_is_sigma'
    def extract(self):
        try:
            t = self.time_data
            m = self.flux_data
            n = len(t)
            
            # get the LS model residuals (for principal frequency)
            lomb_dict = self.fetch_extr('lomb_scargle')
            model = lomb_dict.get('freq1_model',[])
            x = m - model

            delta = t[1:] - t[:-1]

            # get theta
            theta = self.fetch_extr('ar_is_theta')

            # estimate sigma
            z = x[1:] - theta**delta * x[:-1]
            sigma = numpy.sqrt( 1./n * numpy.sum( z**2 / (1-theta**(2*delta))/(1-theta**2)))
            return sigma
        except:
            return 0.0

            # estimate sigma
            
