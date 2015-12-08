import numpy as np
import scipy.stats as stats
from sklearn.linear_model import ElasticNet, ElasticNetCV

def construct_X(t, omegas):
    offsets = [np.ones(len(t))]
    cols = sum(([np.sin(2 * np.pi * omega * t),
                 np.cos(2 * np.pi * omega * t)]
                for omega in omegas), offsets)
    X = (np.vstack(cols)).T
    return X

def ls_lasso(t, y, dy, omegas, l1_ratio=0.99):
    X = construct_X(t, omegas)
    print(X.shape)
    model = ElasticNet(l1_ratio=l1_ratio, alpha=1., fit_intercept=False).fit(X, y)
    return model
