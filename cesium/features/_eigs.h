#include <math.h>

static inline double SQR(double a) {
    return (a == 0.0 ? 0.0 : a*a);
}

static inline double SIGN(double a,double b) {
    return ((b) >= 0.0 ? fabs(a) : -fabs(a));
}

double pythag(double a, double b) {
        double absa,absb;
        absa=fabs(a);
        absb=fabs(b);
        if (absa > absb) return absa*sqrt(1.0+SQR(absb/absa));
        else return (absb == 0.0 ? 0.0 : absb*sqrt(1.0+SQR(absa/absb)));
}

static inline void tred2(double a[], int n, double d[], double e[]) {
        int l,k,j,i;
        double scale,hh,h,g,f;

        for (i=n-1;i>=1;i--) {
                l=i-1;
                h=scale=0.0;
                if (l > 0) {
                        for (k=0;k<=l;k++)
                                scale += fabs(a[k+i*n]);
                        if (scale == 0.0)
                                e[i]=a[l+i*n];
                        else {
                                for (k=0;k<=l;k++) {
                                        a[k+i*n] /= scale;
                                        h += a[k+i*n]*a[k+i*n];
                                }
                                f=a[l+i*n];
                                g=(f >= 0.0 ? -sqrt(h) : sqrt(h));
                                e[i]=scale*g;
                                h -= f*g;
                                a[l+i*n]=f-g;
                                f=0.0;
                                for (j=0;j<=l;j++) {
                                        a[i+j*n]=a[j+i*n]/h;
                                        g=0.0;
                                        for (k=0;k<=j;k++)
                                                g += a[k+j*n]*a[k+i*n];
                                        for (k=j+1;k<=l;k++)
                                                g += a[j+k*n]*a[k+i*n];
                                        e[j]=g/h;
                                        f += e[j]*a[j+i*n];
                                }
                                hh=f/(h+h);
                                for (j=0;j<=l;j++) {
                                        f=a[j+i*n];
                                        e[j]=g=e[j]-hh*f;
                                        for (k=0;k<=j;k++)
                                                a[k+j*n] -= (f*e[k]+g*a[k+i*n]);
                                }
                        }
                } else
                        e[i]=a[l+i*n];
                d[i]=h;
        }
        d[0]=0.0;
        e[0]=0.0;
        for (i=0;i<n;i++) {
                l=i-1;
                if (d[i]) {
                        for (j=0;j<=l;j++) {
                                g=0.0;
                                for (k=0;k<=l;k++)
                                        g += a[k+i*n]*a[j+k*n];
                                for (k=0;k<=l;k++)
                                        a[j+k*n] -= g*a[i+k*n];
                        }
                }
                d[i]=a[i+i*n];
                a[i+i*n]=1.0;
                for (j=0;j<=l;j++) a[i+j*n]=a[j+i*n]=0.0;
        }
}

void tqli(double d[], double e[], int n, double z[])
{
        int m,l,iter,i,k;
        double s,r,p,g,f,dd,c,b;

        for (i=1;i<n;i++) e[i-1]=e[i];
        e[n-1]=0.0;
        for (l=0;l<n;l++) {
                iter=0;
                do {
                        for (m=l;m<n-1;m++) {
                                dd=fabs(d[m])+fabs(d[m+1]);
                                if ((double)(fabs(e[m])+dd) == dd) break;
                        }
                        if (m != l) {
                                if (iter++ == 30) break;
                                g=(d[l+1]-d[l])/(2.0*e[l]);
                                r=pythag(g,1.0);
                                g=d[m]-d[l]+e[l]/(g+SIGN(r,g));
                                s=c=1.0;
                                p=0.0;
                                for (i=m-1;i>=l;i--) {
                                        f=s*e[i];
                                        b=c*e[i];
                                        e[i+1]=(r=pythag(f,g));
                                        if (r == 0.0) {
                                                d[i+1] -= p;
                                                e[m]=0.0;
                                                break;
                                        }
                                        s=f/r;
                                        c=g/r;
                                        g=d[i+1]-p;
                                        r=(d[i]-g)*s+2.0*c*b;
                                        d[i+1]=g+(p=s*r);
                                        g=c*r-b;
                                        for (k=0;k<n;k++) {
                                                f=z[i+1+k*n];
                                                z[i+1+k*n]=s*z[i+k*n]+c*f;
                                                z[i+k*n]=c*z[i+k*n]-s*f;
                                        }
                                }
                                if (r == 0.0 && i >= l) continue;
                                d[l] -= p;
                                e[l]=g;
                                e[m]=0.0;
                        }
                } while (m != l);
        }
}

static inline void get_eigs(int np, double x[], double d[]) {
      double* e = malloc(np * sizeof(double));
      tred2(x,np,d,e);
      tqli(d,e,np,x);
      free(e);
}
