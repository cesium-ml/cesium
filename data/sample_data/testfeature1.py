import numpy as np
try:
    from ..custom_feature_tools import *
except:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from mltsp.custom_feature_tools import *

@myFeature(requires=["t","m"], provides=['period','avg_mag'])
def test_feature(t,m):
    print("test_feature executing.")
    return {'avg_mag': np.average(m), 'period':0}


@myFeature(requires=["t","m","e","period"], provides=['a','b','c'])
def test_feature2(t,m,e,period):
    print("test_feature2 executing.")
    return {'a': 0, 'b':0, 'c':0}


@myFeature(requires=["period","c"], provides=['d','w','f'])
def test_feature3(period,c):
    print("test_feature3 executing.")
    return {'d': 0, 'w':0, 'f':0}


@myFeature(requires=["t","m","e"], provides=['g','h','i'])
def test_feature4(t,m,e):
    print("test_feature4 executing.")
    return {'g': 0, 'h':0, 'i':0}


@myFeature(requires=["f"], provides=['j','k','l'])
def test_feature5(f):
    print("test_feature5 executing.")
    return {'j': 0, 'k':0, 'l':0}


@myFeature(requires=["e"], provides=['q','n','o'])
def test_feature6(e):
    print("test_feature6 executing.")
    return {'q': 0, 'n':0, 'o':0}


if __name__ == "__main__":
    print("testfeature1.py called.")
