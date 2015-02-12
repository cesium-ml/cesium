import re
try:
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen
try:
    from bs4 import BeautifulSoup
except:
    BeautifulSoup = False
import numpy as np
try:
    from matplotlib import pyplot as plt
except:
    pass
import scipy.stats as stats
import pickle as p
#from matplotlib.backends.backend_pdf import PdfPages
import heapq
#import pyPdf
#import lcs_db
import os
import sys
from . import cfg


class lightCurve(object):
    """Time-series data and features object.

    Attributes
    ----------
    epochs : list of float
        List of times of all observations.
    mags : list of float
        List of magnitudes of observations.
    errs : list of float
        List of error estimates.
    avg_mag : float
        Average (mean) magnitude.
    n_epochs : int
        The number of epochs.
    avg_err : float
        Average (mean) of the errors.
    med_err : float
        Median error.
    std_err : float
        Standard deviation of the errors.
    start : float
        Time of first observation.
    end : float
        Time of last observation.
    total_time : float
        Difference between `end` and `start`.
    avgt : float
        Average time between observations.
    cads : list of float
        List of time between successive observations.
    cads_std : float
        Standard deviation of `cads`.
    cads_avg : float
        Mean of `cads`.
    cads_med : float
        Median value of `cads`.
    cad_probs : dict
        Dictionary with time value (int, in minutes) as keys, whose
        corresponding values are the probabilities that the next
        observation is within the specified time of an arbitrary epoch.
        E.g. for a key of 1, the associated value is the probability
        that the next observation is within one minute of an arbitrary
        epoch.
    cad_probs_1 : float
        Probability that the next observation is within one minute of
        an arbitrary epoch.
    ...
    cad_probs_10000000 : float
        Probability that the next observation is within 10000000
        minutes of an arbitrary epoch.
    double_to_single_step : list of float
        List of ratios of time to observation after next to time to
        next observation, for all epochs with index in the interval
        [0, N-3], where N is the total number of epochs.
    med_double_to_single_step : float
        Median of `double_to_single_step`.
    avg_double_to_single_step : float
        Average (mean) of `double_to_single_step`.
    std_double_to_single_step : float
        Standard deviation of `double_to_single_step`.
    all_times : list of float
        List of time intervals to all later observations from each
        epoch.
    all_times_hist : list
        Histogram of `all_times`.
    all_times_bins : list of float
        Bin edges of histogram of `all_times`.
    all_times_hist_peak_val : float
        Peak value of `all_times_hist`.
    all_times_hist_peak_bin : int
        Bin number of peak of `all_times_hist`.
    all_times_hist_normed : list
        `all_times_hist` normalized such that it sums to one.
    all_times_bins_normed : list
        `all_times_bins` normalized such that last bin edge equals one.
    all_times_nhist_numpeaks : int
        Number of peaks in `all_times_hist_normed`.
    all_times_nhist_peaks : list
        List of up to four biggest peaks of `all_times_hist_normed`,
        each being a two-item list: ``[peak_val, bin_index]``.
    all_times_nhist_peak_1_to_2 : float
        Ratio of `all_times_hist` first peak height to second peak
        height.
    ...
    all_times_nhist_peak_3_to_4 : float
        Ratio of `all_times_hist` third peak height to fourth peak
        height.
    all_times_nhist_peak1_bin : int
        Bin number of first peak of `all_times_hist`.
    all_times_nhist_peak4_bin : int
        Bin number of fourth peak of `all_times_hist`.
    all_times_nhist_peak_val : float
        Peak value of `all_times_hist_normed`.
    time_unit : str
        String specifying time unit (e.g. 'day').
    id : str
        dotAstro source id (string).
    classname : str
        Name of class if part of training set.
    ra : float
        Right ascension (decimal degrees).
    dec : float
        Declination (decimal degrees).
    band : str
        Observation band/filter.

    Methods
    -------
    showInfo()
        Print summary of main attributes.
    showAllInfo()
        Print all attribute names and their values.
    allAttrs()
        Print all object attribute names.
    generateFeaturesDict()
        Return dictionary of all feature attributes.

    """

    def __init__(
        self, epochs, mags, errs=[], ra='none', dec='none',
        source_id='none', time_unit='day', classname='unknown',
        band='unknown', features_to_use=[]):
        """Instantiate object and generate features.

        Generates all features described in Attributes section of class
        docstring above that are not provided as parameters to
        constructor.

        Parameters
        ----------
        epochs : list of float
            List of times of all observations.
        mags : list of float
            List of magnitudes of observations.
        errs : list of float, optional
            List of error estimates, defaults to empty list.
        ra : float, optional
            Right ascension (decimal degrees). Defaults to "none".
        dec : float, optional
            Declination (decimal degrees). Defaults to "none".
        source_id : str, optional
            dotAstro source id (string), defaults to "none".
        time_unit : str, optional
            String specifying time unit, defaults to "day".
        classname : str, optional
            Name of class if part of training set, defaults to
            "unknown".
        band : str, optional
            Observation band/filter, defaults to "unknown".
        features_to_use : list, optional
            List of features to generate. Defaults to an empty list, in
            which case all available features are generated.

        """
        self.time_unit = time_unit
        self.id = str(source_id)
        self.classname = classname
        self.start = epochs[0]
        self.end = epochs[-1]
        self.total_time = self.end - self.start
        self.epochs = epochs
        self.n_epochs = len(epochs)
        self.errs = errs
        self.mags = mags
        self.avg_mag = np.average(mags)
        self.ra = ra
        self.dec = dec
        self.band = band
        self.avgt = round((self.total_time)/(float(len(epochs))),3)
        self.cads = []

        self.double_to_single_step = []
        self.all_times = []

        if len(errs) > 0:
            self.avg_err = np.average(errs)
            self.med_err = np.median(errs)
            self.std_err = np.std(errs)
        else:
            self.avg_err = None
            self.med_err = None
            self.std_err = None

        for i in range(len(epochs)):

            # all the deltaTs (time to next obs)
            try:
                self.cads.append(epochs[i+1]-epochs[i])
            except IndexError:
                pass

            # ratio of time to obs after next to time to next obs
            try:
                self.double_to_single_step.append(
                    (epochs[i+2]-epochs[i])/(epochs[i+2]-epochs[i+1]))
            except IndexError:
                pass
            except ZeroDivisionError:
                pass

            # all possible deltaTs ()
            for j in range(1,len(epochs)):
                try:
                    self.all_times.append(epochs[i+j]-epochs[i])
                except IndexError:
                    pass

        self.all_times_std = np.std(self.all_times)
        self.all_times_med = np.median(self.all_times)
        self.all_times_avg = np.average(self.all_times)

        hist, bins = np.histogram(self.all_times,bins=50)
        nhist, bins = np.histogram(self.all_times,bins=50,normed=True)
        self.all_times_hist = hist
        self.all_times_bins = bins
        self.all_times_hist_peak_val = np.max(hist)
        self.all_times_hist_peak_bin = np.where(
            hist == self.all_times_hist_peak_val)[0][0]
        self.all_times_hist_normed = nhist
        self.all_times_bins_normed = bins/np.max(self.all_times)
        self.all_times_nhist_peak_val = np.max(nhist)

        peaks = [] # elements are lists: [peak, index]
        for peak in heapq.nlargest(10,nhist):
            index = np.where(nhist == peak)[0][0]
            try:
                if nhist[index-1] < peak and nhist[index+1] < peak:
                    peaks.append([peak,index])
                elif nhist[index-1] == peak:
                    if nhist[index-2] < peak:
                        peaks.append([peak,index])
                elif nhist[index+1] == peak:
                    if nhist[index+2] < peak:
                        peaks.append([peak,index])
            except IndexError:
                # peak is first or last entry
                peaks.append([peak,index])

        peaks = sorted(peaks,key=lambda x:x[1])

        self.all_times_nhist_peaks = peaks[:4]
        self.all_times_nhist_numpeaks = len(peaks)
        if len(peaks) > 0:
            self.all_times_nhist_peak1_bin = peaks[0][1]
        else:
            self.all_times_nhist_peak1_bin = None
        (self.all_times_nhist_peak_1_to_2, self.all_times_nhist_peak_1_to_3,
            self.all_times_nhist_peak_2_to_3, self.all_times_nhist_peak_1_to_4,
            self.all_times_nhist_peak_2_to_4,
            self.all_times_nhist_peak_3_to_4) = [None,None,None,None,None,None]
        (self.all_times_nhist_peak4_bin, self.all_times_nhist_peak3_bin,
            self.all_times_nhist_peak2_bin) = [None,None,None]
        if len(peaks) >= 2:
            self.all_times_nhist_peak_1_to_2 = peaks[0][0]/peaks[1][0]
            self.all_times_nhist_peak2_bin = peaks[1][1]
            if len(peaks) >= 3:
                self.all_times_nhist_peak_2_to_3 = peaks[1][0]/peaks[2][0]
                self.all_times_nhist_peak_1_to_3 = peaks[0][0]/peaks[2][0]
                self.all_times_nhist_peak3_bin = peaks[2][1]
                if len(peaks) >= 4:
                    self.all_times_nhist_peak_1_to_4 = peaks[0][0]/peaks[3][0]
                    self.all_times_nhist_peak_2_to_4 = peaks[1][0]/peaks[3][0]
                    self.all_times_nhist_peak_3_to_4 = peaks[2][0]/peaks[3][0]
                    self.all_times_nhist_peak4_bin = peaks[3][1]

        self.avg_double_to_single_step = np.average(self.double_to_single_step)
        self.med_double_to_single_step = np.median(self.double_to_single_step)
        self.std_double_to_single_step = np.std(self.double_to_single_step)

        self.cads_std = np.std(self.cads)
        self.cads_avg = np.average(self.cads)
        self.cads_med = np.median(self.cads)

        self.cad_probs = {}
        for time in [1,10,20,30,40,50,100,500,1000,5000,10000,50000,
                     100000,500000,1000000,5000000,10000000]:
            if self.time_unit == 'day':
                self.cad_probs[time] = stats.percentileofscore(
                    self.cads,float(time)/(24.0*60.0))/100.0
            elif self.time_unit == 'hour':
                self.cad_probs[time] = stats.percentileofscore(
                    self.cads,float(time))/100.0

        self.cad_probs_1 = self.cad_probs[1]
        self.cad_probs_10 = self.cad_probs[10]
        self.cad_probs_20 = self.cad_probs[20]
        self.cad_probs_30 = self.cad_probs[30]
        self.cad_probs_40 = self.cad_probs[40]
        self.cad_probs_50 = self.cad_probs[50]
        self.cad_probs_100 = self.cad_probs[100]
        self.cad_probs_500 = self.cad_probs[500]
        self.cad_probs_1000 = self.cad_probs[1000]
        self.cad_probs_5000 = self.cad_probs[5000]
        self.cad_probs_10000 = self.cad_probs[10000]
        self.cad_probs_50000 = self.cad_probs[50000]
        self.cad_probs_100000 = self.cad_probs[100000]
        self.cad_probs_500000 = self.cad_probs[500000]
        self.cad_probs_1000000 = self.cad_probs[1000000]
        self.cad_probs_5000000 = self.cad_probs[5000000]
        self.cad_probs_10000000 = self.cad_probs[10000000]

    def showInfo(self):
        print([self.start,self.end,len(self.epochs),self.avgt])

    def showAllInfo(self):
        for attr, val in list(vars(self).items()):
            print(attr, ":", val)

    def allAttrs(self):
        count = 0
        for attr, val in list(vars(self).items()):
            print(attr)
            count += 1
        print(count, "attributes total.")

    def generate_features_dict(self):
        features_dict = {}
        for attr, val in list(vars(self).items()):
            if attr in cfg.features_list:
                features_dict[attr] = val
        return features_dict


def makePdf(sources):
    """Generate PDF of feature scatter plots for given sources.

    Resulting PDF is saved in working directory.

    Parameters
    ----------
    sources : list of Source
        List of Source objects to include in plots.

    Returns
    -------
    int
        Returns 0 upon successful completion.

    """
    pdf = PdfPages("sample_features.pdf")
    classnames = []
    classname_dict = {}
    x = 2 # number of subplot columns
    y = 3 # number of subplot rows
    for source in sources:
        lc = source.lcs[0]

        if lc.classname not in classnames:
            classnames.append(lc.classname)
            classname_dict[lc.classname] = [lc]
        else:
            classname_dict[lc.classname].append(lc)

        if len(classname_dict[lc.classname]) < 3:

            label = lc.classname + "; ID: " + lc.id
            # all_times histogram:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            ax.set_title(label)
            ax.axis('off')

            ax1 = fig.add_subplot(321)
            ax2 = fig.add_subplot(322)
            ax2.axis('off')
            ax3 = fig.add_subplot(323)
            ax4 = fig.add_subplot(324)
            ax4.axis('off')
            ax5 = fig.add_subplot(325)
            ax6 = fig.add_subplot(326)
            ax6.axis('off')

            hist, bins, other = ax1.hist(lc.all_times,50,normed=True)
            ax1.text(np.max(bins)*0.1,np.max(hist)*0.8,
                     r'Histogram (normed) of all $\Delta$Ts')

            ax2.text(0.0,0.9,(r'$\bullet$med time to next obs: ' +
                              str(np.round(lc.cads_med,4))))
            ax2.text(0.0,0.75,(r'$\bullet$avg time to next obs: ' +
                               str(np.round(lc.avgt,4))))
            ax2.text(0.0,0.6,(r'$\bullet$std dev of time to next obs: ' +
                              str(np.round(lc.cads_std,4))))
            ax2.text(0.0,0.45,(r'$\bullet$med of all $\Delta$Ts: ' +
                               str(np.round(lc.all_times_med,4))))
            ax2.text(0.0,0.3,(r'$\bullet$avg of all $\Delta$Ts: ' +
                              str(np.round(lc.all_times_avg,4))))
            ax2.text(0.0,0.15,(r'$\bullet$std dev of all $\Delta$Ts: ' +
                               str(np.round(lc.all_times_std,4))))

            hist, bins, other = ax3.hist(lc.cads,50)
            ax3.text(np.max(bins)*0.1,np.max(hist)*0.8,
                     r'Hist of time to next obs')

            ax6.text(0.0,0.9,r'$\bullet$Number of epochs: ' + str(lc.n_epochs))
            ax6.text(0.0,0.75,(r'$\bullet$Time b/w first & last obs (days): ' +
                               str(np.round(lc.total_time,2))))
            ax6.text(0.0,0.6,(r'$\bullet$Average error in mag: ' +
                              str(np.round(lc.avg_err,4))))
            ax6.text(0.0,0.45,(r'$\bullet$Median error in mag: ' +
                               str(np.round(lc.med_err,4))))
            ax6.text(0.0,0.3,(r'$\bullet$Std dev of error: ' +
                              str(np.round(lc.std_err,4))))
            ax6.text(0.0,0.15,'')

            ax5.scatter(lc.epochs,lc.mags)

            ax4.text(0.0, 0.9, (r'$\bullet$Avg double to single step ratio: ' +
                                str(np.round(lc.avg_double_to_single_step,3))))
            ax4.text(0.0,0.75,(r'$\bullet$Med double to single step: ' +
                               str(np.round(lc.med_double_to_single_step,3))))
            ax4.text(0.0,0.6,(r'$\bullet$Std dev of double to single step: ' +
                              str(np.round(lc.std_double_to_single_step,3))))
            ax4.text(
                0.0, 0.45,
                (r'$\bullet$1st peak to 2nd peak (in all $\Delta$Ts): ' +
                 str(np.round(lc.all_times_nhist_peak_1_to_2,3))))
            ax4.text(
                0.0, 0.3,
                (r'$\bullet$2ndt peak to 3rd peak (in all $\Delta$Ts): ' +
                 str(np.round(lc.all_times_nhist_peak_2_to_3,3))))
            ax4.text(
                0.0,0.15,
                (r'$\bullet$1st peak to 3rd peak (in all $\Delta$Ts): ' +
                 str(np.round(lc.all_times_nhist_peak_1_to_3,3))))

            pdf.savefig(fig)

    pdf.close()

    pdf = PdfPages('feature_plots.pdf')

    fig = plt.figure()

    ax1 = fig.add_subplot(221)
    ax2 = fig.add_subplot(222)
    ax3 = fig.add_subplot(223)
    ax4 = fig.add_subplot(224)

    plt.subplots_adjust(wspace=0.4,hspace=0.4)

    classnamenum = 0

    colors = ['red','yellow','green','blue','gray','orange','cyan','magenta']
    for classname, lcs in list(classname_dict.items()):
        classnamenum += 1
        print(classname, len(lcs), 'light curves.')
        attr1 = []
        attr2 = []
        attr3 = []
        attr4 = []
        attr5 = []
        attr6 = []
        attr7 = []
        attr8 = []
        for lc in lcs:
            attr1.append(lc.n_epochs)
            attr2.append(lc.avgt)
            attr3.append(lc.cads_std)
            attr4.append(lc.total_time)
            attr5.append(lc.all_times_hist_peak_val)
            attr6.append(lc.cad_probs[5000])
            attr7.append(lc.all_times_nhist_peak_1_to_3)
            attr8.append(lc.all_times_nhist_peak_val)

        ax2.scatter(attr1,attr2,color=colors[classnamenum],label=classname)
        ax1.scatter(attr3,attr4,color=colors[classnamenum],label=classname)
        ax2.set_xlabel('N Epochs')
        ax2.set_ylabel('Avg time to next obs')
        ax1.set_xlabel('Standard dev. of time to next obs')
        ax1.set_ylabel('Time b/w first and last obs')

        ax3.scatter(attr5,attr6,color=colors[classnamenum],label=classname)
        ax4.scatter(attr7,attr8,color=colors[classnamenum],label=classname)
        ax3.set_xlabel(r'All $\Delta$T hist peak val')
        ax3.set_ylabel('Prob time to next obs <= 5000 min')
        ax4.set_xlabel(r'$\Delta$Ts normed hist peak 1 to peak 3')
        ax4.set_ylabel(r'Peak val of all $\Delta$Ts normed hist')

    #ax1.legend(bbox_to_anchor=(1.1, 1.1),prop={'size':6})
    ax2.legend(bbox_to_anchor=(1.1, 1.1),prop={'size':6})
    #ax3.legend(loc='upper right',prop={'size':6})
    #ax4.legend(loc='upper right',prop={'size':6})

    pdf.savefig(fig)

    pdf.close()
    return 0


def generate_lc_snippets(lc):
    """Generate series of snippets of provided time-series data.

    Generates a series of snippets of provided time-series data of
    varying lengths.

    Parameters
    ----------
    lc : lightCurve() object
        lightCurve() object must have valid `epochs`, `mags` and `errs`
        attributes.

    Returns
    -------
    list of lightCurve() objects
        Returns a list of lightCurve() objects whose `epochs`, `mags`
        and `errs` attributes are snippets of the original, with new
        features generated from the resulting TS data snippets.

    """
    epochs,mags,errs = [lc.epochs,lc.mags,lc.errs]
    lc_snippets = []
    n_epochs = len(epochs)
    for binsize in [20,40,70,100,150,250,500,1000,10000]:
        nbins = 0
        if n_epochs > binsize:
            bin_edges = np.linspace(
                0,n_epochs-1,int(round(float(n_epochs)/float(binsize)))+1)
            #for chunk in list(chunks(range(n_epochs),binsize)):
            bin_indices = list(range(len(bin_edges)-1))
            np.random.shuffle(bin_indices)
            for i in bin_indices:
                nbins += 1
                if (int(round(bin_edges[i+1])) -
                        int(round(bin_edges[i])) >= 10 and
                        nbins < 4):
                    lc_snippets.append(lightCurve(
                        epochs[int(round(bin_edges[i])):
                            int(round(bin_edges[i+1]))],
                        mags[int(round(bin_edges[i])):
                            int(round(bin_edges[i+1]))],
                        errs[int(round(bin_edges[i])):
                            int(round(bin_edges[i+1]))],
                        classname=lc.classname))

    return lc_snippets


class Source(object):
    """Time-series data source object.

    Attributes
    ----------
    lcs : list of lightCurve() objects
        List of lightCurve() objects associated with source.
    lc_snippets : list of lightCurve() objects
        List of lightCurve() objects created from snippets of elements
        in `lcs`.
    id : str
        Source ID.
    classname : str
        Source class, if known.

    """
    def __init__(self,id,lcs,classname='unknown',generate_snippets=True):
        """Object constructor.

        Instantiates object and creates attributes. Generates snippets
        of provided light curves if `generate_snippets` parameter is
        True.

        Parameters
        ----------
        id : str
            Source ID.
        lcs : list of lightCurve() objects
            List of lightCurve() objects associated with source.
        classname : str, optional
            Source class, if known. Defaults to "unknown".
        generate_snippets : bool, optional
            Boolean indicating whether to generate snippets of each of
            the provided light curves. Defaults to True.

        """
        self.lcs = []
        self.lc_snippets = []
        self.id = id
        self.classname = classname
        for lc in lcs:
            self.lcs.append(lc)
            if generate_snippets:
                self.lc_snippets.extend(generate_lc_snippets(lc))

    def showInfo(self):
        """Print a human-readable summary of object attributes.

        """
        print("dotAstro ID: " + str(self.id) + "Num LCs: " + str(len(self.lcs)))

    def plotCadHists(self):
        """Plot cadence histograms for all `lcs` attribute elements.

        """
        n_lcs = len(self.lcs)
        if n_lcs > 0:
            x = int(np.sqrt(n_lcs))
            y = n_lcs/x + int(n_lcs%x > 0)
            plotnum = 1
            for lc in self.lcs:
                plt.subplot(x,y,plotnum)
                plt.hist(lc.cads,50,range=(0,np.std(lc.cads)*2.0))
                plt.xlabel('Time to next obs.')
                plt.ylabel('# Occurrences')
                plotnum += 1
            plt.show()
        return

    def put(self, cursor, lc_cursor):
        cursor.execute(
            "INSERT INTO sources VALUES(?, ?)",(self.id, self.classname))
        for lc in self.lcs:
            lc.put(lc_cursor)


def getMultiple(source_ids,classname='unknown'):
    """Create multiple Source() objects from list of dotAstro IDs.

    Pulls time-series data over HTTP to create Source() objects with
    lightCurve() objects as attributes.

    Parameters
    ----------
    source_ids : list of str
        List of dotAstro IDs from which to construct Source() objects.
    classname : str, optional
        Class name of sources, defaults to "unknown".

    Returns
    -------
    list of Source()
        Returns a list of the Source() objects created from the
        provided dotAstro IDs.

    """
    if type(source_ids) == str:
        f = open(source_ids,'r')
        ids = f.read().split()
        f.close()
    elif type(source_ids) == list:
        ids = source_ids

    # assuming dotAstro IDs:
    sources = []
    for id in ids:
        lc = getLcInfo(id,classname)
        if lc: # getLcInfo returns False if no data found
            sources.append(lc)

    return sources


def getLcInfo(id,classname='unknown'):
    """Create Source() object from dotAstro ID.

    Pulls time-series data over HTTP to create Source() object with
    lightCurve() objects as attributes.

    Parameters
    ----------
    id : str
        DotAstro ID from which to construct Source() object.
    classname : str, optional
        Class name of source, defaults to "unknown".

    Returns
    -------
    Source() object
        Returns a Source() object created from the provided dotAstro ID.

    """
    id = str(id)
    isError = False
    if("http" in id):
        url = id
    elif id.isdigit():
        url = "http://dotastro.org/lightcurves/vosource.php?Source_ID=" + id
    try:
        lc = urllib.request.urlopen(url).read()
        if lc.find("<TD>") == -1:
            raise urllib.error.URLError('No data for specified source ID.')

    except (IOError, urllib.error.URLError) as error:
        print("Could not read specified file.", id, error)
        isError = True
        return False
    except Exception as error:
        print("Error encountered.", id, error)
        isError = True
        return False

    if not isError:
        lcs = dotAstroLc(lc,id,classname)
        newSource = Source(id,lcs,classname)
        #print len(lcs), "light curves processed for source", id
        return newSource

    return


def dotAstroLc(lc,id,classname):
    """Return list of lightCurve() objects made from provided data.

    Parameters
    ----------
    lc : str
        XML string containing light curve data.
    id : str
        ID of source.
    classname : str
        Class name of source.

    Returns
    -------
    list of lightCurve() objects
        Returns a list of lightCurve() objects created from each of the
        light curves in provided XML data.

    """
    lcs = []
    numlcs = 0
    data = lc
    soup = BeautifulSoup(data)
    try:
        ra = float(soup('position2d')[0]('value2')[0]('c1')[0]\
            .renderContents())
        dec = float(soup('position2d')[0]('value2')[0]('c2')[0]\
            .renderContents())
    except IndexError:
        print('position2d/value2/c1 or c2 tag not present in light curve file')
        ra, dec = [None,None]
    time_unit = []
    for timeunitfield in soup(ucd="time.epoch"):
        time_unit.append(timeunitfield['unit'])

    for data_table in soup('tabledata'):

        epochs = []
        mags = []
        errs = []

        for row in data_table('tr'):
            tds = row("td")
            epochs.append(float(tds[0].renderContents()))
            mags.append(float(tds[1].renderContents()))
            errs.append(float(tds[2].renderContents()))

        if len(epochs) > 0:
            lcs.append(lightCurve(
                epochs, mags, errs, ra, dec,
                id, time_unit[numlcs], classname))
            numlcs += 1

    return lcs


def getMultipleLocal(filenames,classname='unknown'):
    """Create and return a list of Source() objects from provided data.

    Parameters
    ----------
    filenames : list of str
        List of paths to TS data files.
    classname : str, optional
        Class name of provided TS data sources, defaults to "unknown".

    Returns
    -------
    list of Source() objects
        Returns a list of Source() objects.

    """
    sources = []
    for filename in filenames:
        sources.append(getLocalLc(filename,classname))
    return sources


def csvLc(lcdata,classname='unknown',sep=',',single_obj_only=False):
    """Create and return a lightCurve() object from provided TS data.

    """
    lcdata = lcdata.split('\n')
    epochs = []
    mags = []
    errs = []
    for line in lcdata:
        line = line.replace("\n","")
        if len(line.split()) > len(line.split(sep)):
            sep = ' '
        if len(line) > 0:
            if line[0] != "#":
                if sep.isspace():
                    els = line.split()
                else:
                    els = line.split(sep)
                if len(els) == 3:
                    epochs.append(float(els[0]))
                    mags.append(float(els[1]))
                    errs.append(float(els[2]))
                elif len(els) == 2:
                    epochs.append(float(els[0]))
                    mags.append(float(els[1]))
                else:
                    print(len(els), "elements in row - cvsLc()")
    if len(epochs) > 0:
        if single_obj_only:
            lc = lightCurve(epochs,mags,errs,classname=classname)
        else:
            lc = [lightCurve(epochs,mags,errs,classname=classname)]
        return lc
    else:
        print('csvLc() - No data.')
        return []


def getLocalLc(filename, classname='unknown', sep=',',
               single_obj_only=False, ts_data_passed_directly=False,
               add_errors=False):
    """Generate lightCurve() or Source() object(s) from given TS data.

    Parameters
    ----------
    filename : str
        Path to local file containing time-series data.
    classname : str, optional
        Class name associated with provided time series data, defaults
        to "unknown".
    sep : str, optional
        Delimiting character in time-series data, defaults to comma
        (",").
    single_obj_only : bool, optional
        Boolean indicating whether provided time-series data are
        associated with a single light curve (True) or multiple (False).
        If True, returns a list of feature dictionaries. Defaults to
        False.
    ts_data_passed_directly : bool, optional
        Boolean indicating whether `filename` is a string containing
        raw time series data (True) or not. Defaults to False.
    add_errors : bool, optional
        Boolean indicating whether to add an error value of 1.0 to
        each epoch without pre-existing error values. Defaults to False.

    Returns
    -------
    Source() object
        Returns a new Source() object.

    """
    if ts_data_passed_directly:
        lcdata = filename
        for i in range(len(lcdata)):
            try:
                if len(lcdata[i]) == 2 and add_errors:
                    lcdata[i] = lcdata[i] + ["1.0"]
                lcdata[i] = ','.join(lcdata[i])
            except TypeError:
                for j in range(len(lcdata[i])):
                    lcdata[i][j] = str(lcdata[i][j])
                if len(lcdata[i]) == 2 and add_errors:
                    lcdata[i] = lcdata[i] + ["1.0"]
                lcdata[i] = ','.join(lcdata[i])
    else:
        f = open(filename, 'r')
        lcdata = []
        for line in f.readlines():
            if line.strip() != "":
                if len(line.strip().split(sep)) == 2 and add_errors:
                    line = line.strip()+sep+"1.0"
                lcdata.append(line.strip())
        f.close()
    lcdata = '\n'.join(lcdata)
    if lcdata.find("<Position2D>") > 0 and lcdata.find("xml") > 0:
        lcs = dotAstroLc(lcdata,filename,classname)
    else:
        lcs = csvLc(lcdata,classname,sep,single_obj_only=single_obj_only)
    if single_obj_only:
        return lcs
    else:
        #print len(lcs), "light curves processed for", filename
        newSource = Source(filename,lcs,classname)
        return newSource


def generate_timeseries_features(
    filename, classname='unknown', sep=',', single_obj_only=True,
    ts_data_passed_directly=False, add_errors=True):
    """Generate features dict from given time-series data.

    Parameters
    ----------
    filename : str
        Path to local file containing time-series data.
    classname : str, optional
        Class name associated with provided time series data, defaults
        to "unknown".
    sep : str, optional
        Delimiting character in time-series data, defaults to comma
        (",").
    single_obj_only : bool, optional
        Boolean indicating whether provided time-series data are
        associated with a single light curve (True) or multiple (False).
        If True, returns a list of feature dictionaries. Defaults to
        True.
    ts_data_passed_directly : bool, optional
        Boolean indicating whether `filename` is a string containing
        raw time series data (True) or not. Defaults to False.
    add_errors : bool, optional
        Boolean indicating whether to add an error value of 1.0 to
        each epoch without pre-existing error values. Defaults to True.

    Returns
    -------
    dict
        Dictionary containing generated time series features.

    """
    lc_obj = getLocalLc(
        filename, classname=classname, sep=sep,
        single_obj_only=single_obj_only,
        ts_data_passed_directly=ts_data_passed_directly,
        add_errors=add_errors)
    features_dict = lc_obj.generate_features_dict()
    return features_dict


def dotAstro_to_csv(id):
    """Return CSV time-series data for source with provided DotAstro ID.

    Parameters
    ----------
    id : str
        DotAstro source ID.

    Returns
    -------
    list of str
        Returns a list of strings of CSV-format time-series data (t,m,e),
        each line separated by a newline character.

    """
    id = str(id)
    isError = False
    if("http" in id):
        url = id
    elif id.isdigit():
        url = "http://dotastro.org/lightcurves/vosource.php?Source_ID=" + id
    else:
        print("dotAstro ID not a digit.")
    try:
        lc = urllib.request.urlopen(url).read()
        if lc.find("<TD>") == -1:
            raise urllib.error.URLError('No data for specified source ID.')

    except (IOError, urllib.error.URLError) as error:
        print("Could not read specified file.", id, error)
        isError = True
        return False
    except Exception as error:
        print("Error encountered.", id, error)
        isError = True
        return False

    lcs = []
    numlcs = 0
    lcdata = lc
    soup = BeautifulSoup(lcdata)
    try:
        ra = float(soup('position2d')[0]('value2')[0]('c1')[0]\
             .renderContents())
        dec = float(soup('position2d')[0]('value2')[0]('c2')[0]\
              .renderContents())
    except IndexError:
        print('position2d/value2/c1 or c2 tag not present in light curve file')
        ra, dec = [None,None]
    time_unit = []
    for timeunitfield in soup(ucd="time.epoch"):
        time_unit.append(timeunitfield['unit'])

    for data_table in soup('tabledata'):
        csv_str = ""
        for row in data_table('tr'):
            tds = row("td")
            if len(tds) == 3:
                csv_str += ','.join([
                    str(tds[0].renderContents()),
                    str(tds[1].renderContents()),
                    str(tds[2].renderContents())]) + '\n'

        if len(csv_str) > 0:
            lcs.append(csv_str)
            numlcs += 1

    return lcs
