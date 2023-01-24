# cython: language_level=2

cdef extern from "_lomb_scargle.h":
     void lomb_scargle(int numt, unsigned int numf, int nharm, int detrend_order,
                       double psd[], double cn[], double wth[],
                       double sinx[], double cosx[], double sinx_step[],
                       double cosx_step[], double sinx_back[],
                       double cosx_back[], double sinx_smallstep[],
                       double cosx_smallstep[], double hat_matr[],
                       double hat_hat[], double hat0[],
                       double soln[], double chi0, double freq_zoom,
                       double psdmin, double tone_control,
                       double lambda0[], double lambda0_range[],
                       double Tr[], int ifreq[])
