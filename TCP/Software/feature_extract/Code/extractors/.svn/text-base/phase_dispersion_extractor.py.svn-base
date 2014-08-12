try:
    from ..FeatureExtractor import FeatureExtractor
except:
    import os
    ppath = os.environ.get('PYTHONPATH')
    os.environ.update({'PYTHONPATH': ppath + ":" + os.path.realpath("..")})
    #print os.environ.get("PYTHONPATH")
    from FeatureExtractor import FeatureExtractor

import numpy#, pdb
#from scipy.optimize import fmin
#from common_functions.lomb_scargle_refine import lomb


class phase_dispersion_freq0_extractor(FeatureExtractor):
    '''
    returns the frequency estimated by phase dispersion minimization.

    NOTE: designed to identify correct period of eccentric eclipsing sources.

    by I.Shivvers, June 2012
    '''
    active = True
    extname = 'phase_dispersion_freq0'

    def extract(self):
        try:
            t = self.time_data
            m = self.flux_data
            e = self.rms_data

            # find set of periods to test
            test_periods = self.preSelect_periods()

            # choose best period by minimizing GCV
            GCVs = []
            for iii, period in enumerate(test_periods):
                #print iii,'of', len(self.test_periods), '...'
                p = self.fold(t, period)
                best_GCV, optimal_window = self.minimize_GCV(p, m)
                GCVs.append(best_GCV)
            b_period = test_periods[ numpy.argmin(GCVs) ]
            # return the period with the lowest GCV
            return 1./b_period
        except:
            return 0.0

    # DEFINITIONS
    def fold(self, times, period):
        ''' return phases for <times> folded at <period> '''
        t0 = times[0]
        phase = ((times-t0)%period)/period
        return phase

    def rolling_window(self, a, window):
        """ Call: numpy.mean(rolling_window(observations, n), 1)
        """
        shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
        strides = a.strides + (a.strides[-1],)
        return numpy.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

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
        ''' quick way to pick best GCV value; GCV is not smooth  '''
        windows = numpy.arange(*window_range)
        GCVs = numpy.array( [self.GCV(window, X,Y) for window in windows] )
        best_GCV = numpy.min(GCVs)
        optimal_window = windows[ numpy.argmin(GCVs) ]
        return best_GCV, optimal_window
   
    def preSelect_periods(self, numpeaks=5):
        """ use LS to select trial periods for use in find_period
               returns top <numpeaks> most-likely periods """
        lomb_dict = self.fetch_extr('lomb_scargle')
        psd = lomb_dict.get('freq1_psd',[])
        f0 = lomb_dict.get('freq1_f0',0.)
        df = lomb_dict.get('freq1_df',0.)
        numf = lomb_dict.get('freq1_numf',0.)
        frequencies = numpy.linspace( f0, f0+df*numf, numf )
        periods = 1./frequencies
        peaks_ind = self.find_peaks(psd)
        zpp = zip(psd[peaks_ind], periods[peaks_ind])
        zpp.sort(reverse=True)
        test_periods = numpy.array([zed[1] for zed in zpp[:numpeaks]])
        # return periods and a few harmonics
        return numpy.concatenate( [test_periods, test_periods*2, test_periods*3, test_periods/2., test_periods/3. ] )
    '''
    def preSelect_periods(self, t,m,e, numpeaks=10):
        ### calculate raw psd ###
        # longest period (shortest frequency) is .5*(total time span)
        f0 = 2./(t[-1]-t[0])
        # shortest period (largest frequency) is physically motivated at period = .1 days
        fend = 1./.1
        numf = int(136121)
        df = (fend-f0)/numf
        periods = 1./numpy.arange(f0, fend, df)
        # run the smoothed ls periodogram, and find all of the peaks
        psd,lombdict = lomb(t,m,e, f0, df, numf)
        peaks_ind = self.find_peaks(psd)
        zpp = zip(psd[peaks_ind], periods[peaks_ind])
        zpp.sort(reverse=True)
        test_periods = numpy.array([zed[1] for zed in zpp[:numpeaks]])
        # return periods and a few harmonics
        return numpy.concatenate( [test_periods, test_periods*2, test_periods*3, test_periods/2., test_periods/3. ] )
    '''
    def find_peaks(self, x):
       """ find peaks in x """
       xmid = x[1:-1] # orig array with ends removed
       xm1 = x[2:] # orig array shifted one up
       xp1 = x[:-2] # orig array shifted one back
       return numpy.where(numpy.logical_and(xmid > xm1, xmid > xp1))[0] + 1


class ratio_PDM_LS_freq0_extractor(FeatureExtractor):
    ''' returns the ratio of phase_dispersion-estimated and lomb_scargle-estimated frequencies '''
    active = True
    extname = 'ratio_PDM_LS_freq0'
    def extract(self):
        try:
            pdm_freq = self.fetch_extr('phase_dispersion_freq0')
            lomb_dict = self.fetch_extr('lomb_scargle')
            LS_freq = lomb_dict.get('freq1_harmonics_freq_0',0.)
            return pdm_freq/LS_freq
        except:
            return 0.0

