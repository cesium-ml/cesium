import os,sys
from numpy import median
from ..FeatureExtractor import FeatureExtractor, InterExtractor

from .....Algorithms.qso_fit import qso_fit


#class qso_extractor(FeatureExtractor):  # Using this will add a 'qso' feature in vosource xml whose value is a string representation of the returned od dict.  (using internal_use_only=False, active=False)
class qso_extractor(InterExtractor):
    """ calculates the skew of the signal using scipy.stats.skew
    biased skew?"""
    internal_use_only = False # if set True, then seems to run all qso code for each sub-feature
    active = True # if set False, then seems to run all qso code for each sub-feature
    extname = 'qso' #extractor's name
    def extract(self):
        y0 = 19.
        y = self.flux_data - median(self.flux_data) + y0
        try:
            od = qso_fit(self.time_data,
                         y,
                         self.rms_data,filter='g')
        except:
            self.ex_error(text="qso_extractor.qso_extractor()")

            #res = od['chi2_qso/nu'],od['chi2_qso/nu_NULL']
            # QSO-like:  res[0]<~2
            # non-QSO: res[1]/res[0]<~2
        return od


class qso_generic(FeatureExtractor):
    """ Generic qso extractor grabs value from dictionary   """
    internal_use_only = False
    active = True
    extname = 'to_be_overloaded' # identifier used in final extracted value dict.
    qso_key = 'to_be_overloaded'
    def extract(self):
        qso_dict = self.fetch_extr('qso')
        if self.qso_key in qso_dict:
            return qso_dict[self.qso_key]
        else:
            self.ex_error('qso_extractor dictionary does not have key %s' % (self.qso_key))

##### Nat has converged upon the following being the most significant featues,
#    Joey believes it is best to jut use these features only (so now the others are disabled in
#       __init__.py and qso_extractor.py

class qso_log_chi2_qsonu_extractor(qso_generic):
    """ qso_log_chi2_qsonu """
    extname = "qso_log_chi2_qsonu"
    qso_key = "log_chi2_qsonu"

class qso_log_chi2nuNULL_chi2nu_extractor(qso_generic):
    """ qso_log_chi2nuNULL_chi2nu """
    extname = "qso_log_chi2nuNULL_chi2nu"
    qso_key = "log_chi2nuNULL_chi2nu"

#####

### eventually get rid of:
#class qso_lvar_extractor(qso_generic):
#   """ qso_lvar """
#   extname = "qso_lvar"
#   qso_key = "lvar"

### eventually get rid of:
#class qso_ltau_extractor(qso_generic):
#   """ qso_ltau """
#   extname = "qso_ltau"
#   qso_key = "ltau"

### eventually get rid of:   (since is not related to QSO classifier)
#class qso_chi2nu_extractor(qso_generic):
#   """ qso_chi2nu """
#   extname = "qso_chi2nu"
#   qso_key = "chi2/nu"

#class qso_chi2_qsonu_extractor(qso_generic):
#   """ qso_chi2_qsonu """
#   extname = "qso_chi2_qsonu"
#   qso_key = "chi2_qso/nu"

#class qso_chi2_qso_nu_NULL_extractor(qso_generic):
#   """ chi2_qso_nu_NULL """
#   extname = "qso_chi2_qso_nu_NULL"
#   qso_key = "chi2_qso/nu_NULL"

#class qso_signif_qso_extractor(qso_generic):
#   """ qso_signif_qso """
#   extname = "qso_signif_qso"
#   qso_key = "signif_qso"

#class qso_signif_not_qso_extractor(qso_generic):
#   """ qso_signif_not_qso """
#   extname = "qso_signif_not_qso"
#   qso_key = "signif_not_qso"

#class qso_signif_vary_extractor(qso_generic):
#   """ qso_signif_vary """
#   extname = "qso_signif_vary"
#   qso_key = "signif_vary"

#class qso_chi2qso_nu_nuNULL_ratio_extractor(qso_generic):
#   """ qso_chi2qso_nu_nuNULL_ratio """
#   extname = "qso_chi2qso_nu_nuNULL_ratio"
#   qso_key = "chi2qso_nu_nuNULL_ratio"

