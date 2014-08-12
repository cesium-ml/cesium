from numpy import ones,empty,median,sqrt,mean,abs,sign


def	stetson_mean( x, weight=100.,alpha=2.,beta=2.,tol=1.e-6,nmax=20):
  """An iteratively weighted mean"""

  x0 = median( x )

  for i in xrange(nmax):
    resid = x - x0
    resid_err = abs(resid)*sqrt(weight)
    weight1 = weight/(1. + (resid_err/alpha)**beta)
    weight1 /= weight1.mean()
    diff = mean( x*weight1 ) - x0
    x0 += diff
    if (abs(diff) < tol*abs(x0) or abs(diff) < tol): break


  return x0


def	stetson_j(x,y=[],dx=0.1,dy=0.1):
  """Robust covariance statistic between pairs of observations x,y
       whose uncertainties are dx,dy.  if y is not given, calculates
       a robust variance for x."""

  nels = len(x)

  x0 = stetson_mean(x, 1./dx**2)
  delta_x = sqrt(nels / (nels - 1.)) * (x - x0) / dx

  if (y!=[]): 
    y0 = stetson_mean(y, 1./dy**2)
    delta_y = sqrt(nels / (nels - 1.)) * (y - y0) / dy
    p_k = delta_x*delta_y
  else:
    p_k = delta_x**2-1.

  return mean( sign(p_k) * sqrt(abs(p_k)) ) 


def	stetson_k(x,dx=0.1):
  """A kurtosis statistic."""

  nels = len(x)

  x0 = stetson_mean(x, 1./dx**2)

  delta_x = sqrt(nels / (nels - 1.)) * (x - x0) / dx

  return 1./0.798 * mean( abs(delta_x) ) / sqrt( mean(delta_x**2) )
