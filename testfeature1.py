from custom_feature_tools import *
import numpy as np


@myFeature(requires=["t","m"], provides=['period','avg_mag'])
def test_feature(t,m):
    print "test_feature executing."
    return {'avg_mag': np.average(m), 'period':0}


@myFeature(requires=["t","m","e","period"], provides=['a','b','c'])
def test_feature2(t,m,e,period):
    print "test_feature2 executing."
    return {'a': 0, 'b':0, 'c':0}


@myFeature(requires=["period","c"], provides=['d','w','f'])
def test_feature3(period,c):
    print "test_feature3 executing."
    return {'d': 0, 'w':0, 'f':0}


@myFeature(requires=["t","m","e"], provides=['g','h','i'])
def test_feature4(t,m,e):
    print "test_feature4 executing."
    return {'g': 0, 'h':0, 'i':0}


@myFeature(requires=["f"], provides=['j','k','l'])
def test_feature5(f):
    print "test_feature5 executing."
    return {'j': 0, 'k':0, 'l':0}


@myFeature(requires=["e"], provides=['q','n','o'])
def test_feature6(e):
    print "test_feature6 executing."
    return {'q': 0, 'n':0, 'o':0}


if __name__=="__main__":
    import lc_tools
    tmestr = lc_tools.dotAstro_to_csv(215156)
    all_lines = tmestr[0].strip().split("\n")
    t,m,e=[[],[],[]]
    for line in all_lines:
        ti,mi,ei = line.split(",")
        t.append(float(ti)); m.append(float(mi)); e.append(float(ei))
    print feature(t=t,m=m,e=e)
