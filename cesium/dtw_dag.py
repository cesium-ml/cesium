# An implementation of a dynamic time warping algorithm based on this paper:
# http://knight.cis.temple.edu/~vasilis/Courses/CIS664/Papers/PKDD05.pdf

import networkx as nx
import numpy as np
from scipy.spatial.distance import euclidean


"""
TODO:
1) write a node class to fix same value problem
2) finish up graph construction. use currentrow idea, increment
3) implement shortest distance
4) write tests
"""


def getDistanceMatrix(x, y, dist):
    """
            Inputs:
                    x: time series
                    y: time series
                    dist: a distance metric
            Outputs:
                    D: the distance matrix of the two time series
            Description:
                    Returns the distance matrix given timeseries x and y.
    """
    if not x or not y:
        print("Inputs cannot be none")
        return None
    if dist == None:
        dist = _defaultdist
    row = min(len(x), len(y))
    col = max(len(x), len(y))
    D = np.zeros(shape=(row, col))
    for i in range(row):
        for j in range(col):
            D[i, j] = dist(x[i], y[j])
    return D


def constructGraph(D, cost=linkcost):
    """
        Inputs:
                D: a distance matrix
                cost: a cost function that computes 'distances' between nodes in the dag
        Output:
                A networkx graph where distances between two notes are defined
                by linkcost
        Description:
        		Creates a graph from D where two notes R_(i,j) and R_(k,l) have an edge if and only if:
        			1) k - i == 1
					2) j < l
				Essentially creates a graph in which every row must be represented, but columns can be
				skipped.
    """

    row, col = D.shape
    diff = col - row
    # finding sources of graphs to be computed.
    sources = D[0, :diff]
    graphList = []
    currentRow = 1
    # adding first level of children
    for i in range(len(sources)):
        G = nx.DiGraph()
        children = find_children(0, i, col)
        edges = ()


def find_children(i, j):
    row, col = D.shape
    # not reached boundaries of the distance matrix
    if i + 1 < row and j + 1 < col:
        return [(i + 1, k) for k in range(j + 1, n)]
    else:
        return []


def findShortestPath(G):


def linkcost(x, y):
	""" Default cost of edges between nodes"""
    return y ^ 2


def _defaultdist(x, y):
	""" default distance metric: distance between two points """
    return x - y
