from numpy import ones,sqrt

def linfit(x,y,dy=[]):
    """
    m = a+b*x
    minimize chi^2 = Sum (y-m)^2/dy^2
    """
    lx=len(x)
    if (dy==[]):
        dy = ones(lx,dtype='float32')

    wt = 1./dy**2
    ss = wt.sum()
    sx = (wt * x).sum()
    sy = (wt * y).sum()
    t =  (x - sx/ss) / dy
    b = (t * y / dy).sum()

    st2 = (t*t).sum()

    # parameter estimates
    b = b / st2
    a = (sy - sx * b) / ss

    # error estimates
    sdeva = sqrt((1. + sx * sx / (ss * st2)) / ss)
    sdevb = sqrt(1. / st2)
    covar = -sx/(ss*st2)
    covar = [[sdeva**2, covar], [covar, sdevb**2]]

    return (a,b,covar)
