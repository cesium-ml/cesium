# cython: language_level=2

from _lomb_scargle cimport lomb_scargle as _lomb_scargle

cimport numpy as cnp
import numpy as np

def lomb_scargle(int numt, unsigned int numf, int nharm, int detrend_order,
                 double[:] psd, double[:] cn, cnp.ndarray wth,
                 double[:] sinx, double[:] cosx, double[:] sinx_step,
                 double[:] cosx_step, double[:] sinx_back,
                 double[:] cosx_back, double[:] sinx_smallstep,
                 double[:] cosx_smallstep, double[:, :] hat_matr,
                 double[:, :] hat_hat, double[:, :] hat0,
                 double[:] soln, double chi0, double freq_zoom,
                 double psdmin, double tone_control,
                 cnp.ndarray[dtype=double, ndim=0] lambda0,
                 double[:] lambda0_range,
                 cnp.ndarray[dtype=double, ndim=0] Tr,
                 cnp.ndarray[dtype=cnp.int32_t, ndim=0] ifreq):

    assert wth.dtype == np.double

    _lomb_scargle(numt, numf, nharm, detrend_order, &psd[0], &cn[0],
                  <double*>(wth.data), &sinx[0], &cosx[0], &sinx_step[0],
                  &cosx_step[0], &sinx_back[0], &cosx_back[0],
                  &sinx_smallstep[0], &cosx_smallstep[0], &hat_matr[0, 0],
                  &hat_hat[0, 0], &hat0[0, 0],
                  &soln[0], chi0, freq_zoom, psdmin, tone_control,
                  <double*>(lambda0.data), &lambda0_range[0],
                  <double*>(Tr.data), <int*>(ifreq.data))
