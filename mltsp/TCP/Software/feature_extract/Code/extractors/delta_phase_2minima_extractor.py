try:
    from ..FeatureExtractor import FeatureExtractor
except:
    import os
    ppath = os.environ.get('PYTHONPATH')
    os.environ.update({'PYTHONPATH': ppath + ":" + os.path.realpath("..")})
    #print os.environ.get("PYTHONPATH")
    from FeatureExtractor import FeatureExtractor

import numpy#, pdb
from scipy.optimize import fmin
try:
    import matplotlib.pyplot as plt
except:
    pass

class delta_phase_2minima_extractor(FeatureExtractor):
    '''
    returns a best guess of the phase difference between the two
    lowest minima of a lightcurve.

    only relevant for eclipsing sources, and best used 
    to identify orbital eccentricity

    author: I.Shivvers, June 2012
    '''
    active = True
    extname = 'delta_phase_2minima'
    def extract(self):
        try:
            # get info
            t = self.time_data
            m = self.flux_data
            pdm_period = 1./self.fetch_extr('phase_dispersion_freq0')
            p = self.fold(t, pdm_period)
            
            # find the proper window for the model
            best_GCV, optimal_window = self.minimize_GCV(p, m)
            mins = self.findMins(p,m, optimal_window)
            val = abs(mins[0]-mins[1])
            if val > .5: val = 1.-val  # keep between 0. and .5
            if val == 0.: val = .5  # only found one minimum; probably got the period wrong by factor of 2
            return val
        except:
            return 0.0

    def findMins(self, p, m, optimal_window):
        """
        Find and return the phase of two lowest minima of unsmoothed data
        If only one minima, returns that phase twice.
        Couched in error-catching, so that it returns 0.,0. if it can't
        make sense of the specific LC  """
        try:
            # calculate smoothed model
            bandwidth = float(optimal_window)/len(p)
            model = self.kernelSmooth(p, m, bandwidth)
            # resort into proper order
            zpm = zip(p, model)
            zpm.sort()
            zpm_arr = numpy.array(zpm)
            phs = zpm_arr[:,0]
            model = zpm_arr[:,1]
            # identify and rank the peaks
            peaks_ind = self.find_peaks(model)
            zppi = zip(model[peaks_ind], phs[peaks_ind], peaks_ind)
            zppi.sort(reverse=True)
            # only report a minima as seperate if the model goes back past the mean and returns in between them
            threshold = numpy.mean(model)
            min1 = zppi[0]
            min2 = zppi[0]
            for zed in zppi[1:]:
                test_values = model[ min([zed[2], min1[2]]): max([zed[2], min1[2]])]
                if min(test_values) < threshold and zed[0] > threshold:
                    min2 = zed
                    break
            return [min1[1], min2[1]]
        except (IndexError, UnboundLocalError):
            return [0., 0.]

    def fold(self, times, period):
        ''' return phases for <times> folded at <period> '''
        t0 = times[0]
        phase = ((times-t0)%period)/period
        return phase

    def rolling_window(self, b, window):
        """ Call: numpy.mean(rolling_window(observations, n), 1)
        """
        # perform smoothing using strides trick
        shape = b.shape[:-1] + (b.shape[-1] - window + 1, window)
        strides = b.strides + (b.strides[-1],)
        return numpy.lib.stride_tricks.as_strided(b, shape=shape, strides=strides)

    def GCV(self, window, X,Y):
        # put in proper order
        zpm = zip(X,Y)
        zpm.sort()
        zpm_arr = numpy.array(zpm)
        phs = zpm_arr[:,0]
        mags = zpm_arr[:,1]
        # handle edges properly by extending array in both directions
        if window>1:
            b = numpy.concatenate((mags[-window/2:], mags, mags[:window/2-1]))
        else:
            b = mags
        # calculate smoothed model and corresponding smoothing matrix diagonal value
        model = numpy.mean(self.rolling_window(b, window), 1)
        Lii = 1./window
        # return the Generalized Cross-Validation criterion
        GCV = 1./len(phs) * numpy.sum( ((mags-model)/(1.-Lii))**2 )
        return GCV

    def minimize_GCV(self,X,Y, window_range=(10,50,2)):
        ''' quick way to pick best GCV value '''
        windows = numpy.arange(*window_range)
        GCVs = numpy.array( [self.GCV(window, X,Y) for window in windows] )
        best_GCV = numpy.min(GCVs)
        optimal_window = windows[ numpy.argmin(GCVs) ]
        return best_GCV, optimal_window

    def GaussianKernel(self, x):
        return (1./numpy.sqrt(2.*numpy.pi)) * numpy.exp(-x**2 / 2.)

    def kernelSmooth(self, X, Y, bandwidth):
        ''' slow implementation of gaussian kernel smoothing '''
        L = numpy.zeros([len(Y),len(X)])
        diags = []
        for i in range(len(X)):
            diff = abs(X[i] - X)
            # wrap around X=1; i.e. diff cannot be more than .5
            diff[diff>.5] = 1. - diff[diff>.5]
            # renormalize, and operate on l vector
            l = diff/bandwidth
            # calculate the Gaussian for the values within 4sigma and plug it in
            # anything beyond 4sigma is basically zero
            tmp = self.GaussianKernel(l[l<4])
            diags.append(numpy.max(tmp))
            L[i,l<4] = tmp/numpy.sum(tmp)
        # model is the smoothing matrix dotted into the data
        return numpy.dot(L, Y.T)

    def find_peaks(self, x):
        """ find peaks in <x> """
        xmid = x[1:-1] # orig array with ends removed
        xm1 = x[2:] # orig array shifted one up
        xp1 = x[:-2] # orig array shifted one back
        return numpy.where(numpy.logical_and(xmid > xm1, xmid > xp1))[0] + 1
