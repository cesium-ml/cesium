#include <math.h>
#include "_eigs.h"

static inline void copy_sincos (int numt, double sinx0[], double cosx0[], double sinx[], double cosx[]) {
    int i;
    for (i=0;i<numt;i++) {
        sinx[i] = sinx0[i];
        cosx[i] = cosx0[i];
    }
}

static inline void update_sincos (int numt, double sinx0[], double cosx0[], double sinx[], double cosx[], int offset) {
    int i1, i;
    double tmp;
    for (i=0;i<numt;i++) {
        i1 = i+offset;
        sinx[i1] = cosx0[i]*(tmp=sinx[i]) + sinx0[i]*cosx[i];
        cosx[i1] = cosx0[i]*cosx[i] - sinx0[i]*tmp;
    }
}

static inline double _lomb_scargle(int numt, double cn[], double sinx[], double cosx[], double st, double ct, double cst) {
  double cs=0.,s2=0.,c2=0.,sh=0.,ch=0.,px=0.,detm;
  int i;
  for (i=0;i<numt;i++) {
    cs += cosx[i]*sinx[i];
    c2 += cosx[i]*cosx[i];
    sh += sinx[i]*cn[i];
    ch += cosx[i]*cn[i];
  }
  cs -= cst; s2 = 1-c2-st; c2 -= ct;
  detm = c2*s2 - cs*cs;
  if (detm>0) px = ( c2*sh*sh - 2.*cs*ch*sh + s2*ch*ch ) / detm;
  return px;
}

static inline void calc_dotprod(int numt, double sinx[], double cosx[], double wt[], int dord, double *st, double *ct) {
    int i;
    unsigned long n2=numt*dord;
    for (*st=0,*ct=0,i=0;i<numt;i++) {
        *st += sinx[i]*wt[i + n2];
        *ct += cosx[i]*wt[i + n2];
    }
}

static inline double do_lomb(int numt, int detrend_order, double cn[], double sinx[], double cosx[], double wth[]) {
    int i;
    double st,cst,ct,st0,ct0;
    for (i=0,ct=0,st=0,cst=0;i<=detrend_order;i++) {
        calc_dotprod(numt,sinx,cosx,wth,i,&st0,&ct0);
        st += st0*st0; ct += ct0*ct0; cst += st0*ct0;
    }
    return _lomb_scargle(numt,cn,sinx,cosx,st,ct,cst);
}

static inline double do_lomb_zoom(int numt, int detrend_order, double *cn, double *sinx, double *cosx, double *sinx1, double *cosx1, double *sinx_back, double *cosx_back, double *sinx_smallstep, double *cosx_smallstep, double *wth, double freq_zoom, int *ifreq) {
    int i;
    double px,pxmax=0.;
    copy_sincos(numt,sinx,cosx,sinx1,cosx1);
    update_sincos(numt, sinx_back, cosx_back, sinx1, cosx1, 0);
    for (i=0;i<freq_zoom;i++) {
        px = do_lomb(numt,detrend_order,cn,sinx1,cosx1,wth);
        if (px>pxmax) {
            pxmax=px;
            *ifreq = i;
        }
        update_sincos(numt, sinx_smallstep, cosx_smallstep, sinx1, cosx1, 0);
    }
    copy_sincos(numt,sinx,cosx,sinx1,cosx1);
    if (*ifreq<freq_zoom/2.) {
        update_sincos(numt, sinx_back, cosx_back, sinx1, cosx1, 0);
        for (i=0;i<*ifreq;i++) update_sincos(numt, sinx_smallstep, cosx_smallstep, sinx1, cosx1, 0);
    } else {
        for (i=0;i<*ifreq-freq_zoom/2.;i++) update_sincos(numt, sinx_smallstep, cosx_smallstep, sinx1, cosx1, 0);
    }
    return px;
}

static inline void def_hat(int numt, int nharm, int detrend_order, double hat_matr[], double hat0[], double sinx[], double cosx[], double wt[], double cn[], double hat_hat[], double vec[], double lambda0) {
    int i,j=numt*nharm,k,npar=2*nharm,dord1=detrend_order+1;
    double* sx0 = malloc(numt * sizeof(double));
    double* cx0 = malloc(numt * sizeof(double));
    double ct, st, sum;
    for (i=0;i<numt;i++) {
        sx0[i] = (hat_matr[i]=sinx[i])/wt[i]; cx0[i] = (hat_matr[i+j]=cosx[i])/wt[i];
    }
    for (j=0;j<nharm-1;j++) {
        update_sincos(numt,sx0,cx0,hat_matr+j*numt,hat_matr+(j+nharm)*numt,numt);
        for (i=0;i<=detrend_order;i++) calc_dotprod(numt,hat_matr+j*numt,hat_matr+(j+nharm)*numt,wt,i,&hat0[i+j*dord1],&hat0[i+(j+nharm)*dord1]);
    }
    for (i=0;i<=detrend_order;i++) calc_dotprod(numt,hat_matr+j*numt,hat_matr+(j+nharm)*numt,wt,i,&hat0[i+j*dord1],&hat0[i+(j+nharm)*dord1]);
    for (j=0;j<npar;j++) {
        for (k=j;k<npar;k++) {
            for (sum=0,i=0;i<numt;i++) sum += hat_matr[i+j*numt]*hat_matr[i+k*numt];
            for (i=0;i<=detrend_order;i++) sum -= hat0[i+j*dord1]*hat0[i+k*dord1];
            hat_hat[k+j*npar] = sum;
        }
    }
    for (j=0;j<npar;j++) {
        ct = (1.+(j%nharm)); ct*=ct;
        for (sum=0,i=0;i<numt;i++) sum += hat_matr[i+j*numt]*cn[i];
        vec[j] = sum/ct;
        for (k=j;k<npar;k++) {
            st = (1.+(k%nharm)); st*=st;
            hat_hat[k+j*npar] /= (ct*st);
            hat_hat[j+k*npar] = hat_hat[k+j*npar];
        }
        hat_hat[j+j*npar] += numt*lambda0;
    }
    free(sx0);
    free(cx0);
}

static inline double optimize_px(int n, int numt, double p[], double hat_hat[], double eigs[], double *lambda0, double *lambda0_range, double chi0, double tc, double *Trace) {
    int i,j,k,niter=50;
    double px,lambda,dlambda,lambda_best,eigs1,px_max=0.,start=lambda0_range[0],stop=lambda0_range[1];
    double s1,s2,s3,tcn=tc/numt,Tr,Tr0=(1-3./numt)/(1.+tcn);
    double* v = malloc(n * sizeof(double));
    double* m = malloc(n * n * sizeof(double));

    for (i=0;i<n;i++) {
      for (j=i;j<n;j++) m[j*n + i] = 0.;
    }
    for (k=0;k<n;k++) {
        s1 = 1.+(k%(n/2)); s1*=s1; s1*=s1;
        for (i=0;i<n;i++) {
            for (j=i;j<n;j++) m[j*n + i] += hat_hat[i+k*n]*hat_hat[j+k*n]/s1;
        }
    }
    lambda = start; dlambda = exp(log(stop/start)/niter);
     for (k=0;k<3;k++) {
        for (j=0;j<=niter;j++) {
          Tr = 1-2.*n/numt; px=chi0; s1=0; s2=0, s3=0;
          for (i=0;i<n;i++) {
              eigs1 = eigs[i] + numt*(lambda-(*lambda0));
              Tr += 2.*lambda/eigs1;
              s1 += p[i]*(v[i]=p[i]/eigs1);
              s2 += p[i]*v[i]/eigs1;
              s3 += v[i]* m[i*n + i]* v[i];
              for (k=0;k<i;k++) s3 += 2.*v[i] *m[i*n + k] *v[k];
           }
           px = chi0  - (chi0-s1-s2*numt*lambda)*(1.+tcn*(s2/s3))*Tr0/Tr;
           if (px>px_max && Tr>0) {
               px_max = px;
               lambda_best = lambda;
               *Trace = Tr;
           }
           lambda *= dlambda;
        }
        if (lambda_best-1.e-5>start) start=lambda_best/dlambda;
        else break;
        if(lambda_best+1.e-5<stop) stop = lambda_best*dlambda;
        else break;
        dlambda = exp(log(stop/start)/niter);
    }
    *lambda0 = lambda_best;
    free(v);
    free(m);
    return px_max;
}

static inline void inv_hat(int n, double hat_hat[], double vec[], double vec1[], double eigs[], double lam0, double lam) {
    int i,j,k;
    double sum;
    double* tmp = malloc(n * n * sizeof(double));
    for (i=0;i<n;i++) {
        for (j=i;j<n;j++) {
            for (sum=0,k=0;k<n;k++) sum += hat_hat[k+i*n]*hat_hat[k+j*n]/(eigs[k]+lam-lam0);
            tmp[i*n + j] = sum;
        }
    }
    for (i=0;i<n;i++) {
        for (j=i;j<n;j++) hat_hat[j+i*n] = hat_hat[i+j*n] = tmp[i*n + j];
        for (sum=0,j=0;j<n;j++) sum += hat_hat[j+i*n]*vec[j];
        vec1[i] = sum;
    }
    free(tmp);
}

static inline double refine_psd(int numt, int nharm, int detrend_order, double hat_matr[], double hat0[], double hat_hat[], double sinx[], double cosx[], double wt[], double cn[], double vec1[], double *lambda0, double *lambda0_range, double chi0, double tc, double *Tr, int inv) {
    int i,j,npar=2*nharm;
    double sum,px,lambda00=*lambda0;
    double* p = malloc(npar * sizeof(double));
    double* vec = malloc(npar * sizeof(double));
    double* eigs = malloc(npar * sizeof(double));
    def_hat(numt,nharm,detrend_order,hat_matr,hat0,sinx,cosx,wt,cn,hat_hat,vec,*lambda0);
    get_eigs(npar,hat_hat,eigs);
    for (i=0;i<npar;i++) {
        for (sum=0,j=0;j<npar;j++) sum += hat_hat[i+j*npar] * vec[j];
        p[i] = sum;
    }
    px = optimize_px(npar,numt,p,hat_hat,eigs,lambda0,lambda0_range,chi0,tc,Tr);
    if (inv==1) inv_hat(npar,hat_hat,vec,vec1,eigs,numt*lambda00,numt*(*lambda0));
    free(p);
    free(vec);
    free(eigs);
    return px;
}

void lomb_scargle(int numt, unsigned int numf, int nharm, int detrend_order,
                  double psd[], double cn[], double wth[], double sinx[],
                  double cosx[], double sinx_step[], double cosx_step[],
                  double sinx_back[], double cosx_back[],
                  double sinx_smallstep[], double cosx_smallstep[],
                  double hat_matr[], double hat_hat[],
                  double hat0[], double soln[], double chi0,
                  double freq_zoom, double psdmin, double tone_control,
                  double lambda0[], double lambda0_range[],
                  double Tr[], int ifreq[])
{
  int ifr=(int)(freq_zoom)/2;
  unsigned long j;
  unsigned long jmax=0;
  *ifreq = ifr;
  double psdmax=0.,psd0max=0.,Trace,lambda;
  double* sinx1 = malloc(numt * sizeof(double));
  double* cosx1 = malloc(numt * sizeof(double));
  double* sinx2 = malloc(numt * sizeof(double));
  double* cosx2 = malloc(numt * sizeof(double));
  for (j=0;j<numf;j++) {
      // do a simple lomb-scargle, sin+cos fit
      psd[j] = do_lomb(numt,detrend_order,cn,sinx,cosx,wth);
      if (psd[j]>psd0max && psdmax==0) {
          psd0max = psd[j];
          copy_sincos(numt,sinx,cosx,sinx2,cosx2);
          jmax = j;
      }
      // refine the fit around significant sin+cos fits
      if (psd[j]>(double)psdmin) {
          // first let the frequency vary slightly
          do_lomb_zoom(numt,detrend_order, cn, sinx, cosx, sinx1, cosx1, sinx_back, cosx_back, sinx_smallstep, cosx_smallstep, wth, freq_zoom, &ifr);
          lambda = *lambda0;
          // now fit a multi-harmonic model with generalized cross-validation to avoid over-fitting
          psd[j] = refine_psd(numt,nharm,detrend_order,hat_matr,hat0,hat_hat,sinx1,cosx1,wth,cn,soln,&lambda,lambda0_range,chi0,tone_control,&Trace,0);
          if (psd[j]>psdmax) {
              copy_sincos(numt,sinx1,cosx1,sinx2,cosx2);
              psdmax=psd[j];
              *ifreq = ifr;
              jmax = j;
          }
      }
      update_sincos(numt, sinx_step, cosx_step, sinx, cosx, 0);
  }
  // finally, rerun at the best-fit period so we get some statistics
  psd[jmax] = refine_psd(numt,nharm,detrend_order,hat_matr,hat0,hat_hat,sinx2,cosx2,wth,cn,soln,lambda0,lambda0_range,chi0,tone_control,Tr,1);
  free(sinx1);
  free(cosx1);
  free(sinx2);
  free(cosx2);
}
