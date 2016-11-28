# An implementation of a dynamic time warping algorithm based on this paper:
# http://knight.cis.temple.edu/~vasilis/Courses/CIS664/Papers/PKDD05.pdf

import networkx as nx
import numpy as np

"""
TODO:
2) labeling nodes in a consistent fashion.
3) implement shortest distance - use in built networkx method. [DONE]
4) write tests
"""


def _defaultdist(x, y):
    """ default distance metric: distance between two points """
    return y - x


def getDistanceMatrix(x, y, dist=_defaultdist):
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
    if x is None or y is None:
        print("Inputs cannot be none")
        return None
    if len(x) < len(y):
        col = y
        row = x
    else:
        col = x
        row = y
    D = np.zeros(shape=(len(row), len(col)))
    for i in range(len(row)):
        for j in range(len(col)):
            D[i, j] = dist(row[i], col[j])
    return D


def linkcost(x, y):
    """ Default cost of edges between nodes"""
    return (y**2)


def construct_graph(D, cost=linkcost):
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
                Essentially creates a graph in which every row must be represented, but columns can be  skipped.
    """

    row, col = D.shape
    diff = col - row
    graphList = [nx.DiGraph() for i in range(diff)]
    # sourceList = D[0, :diff]
    # sourceDict = {}
    # add sources and their locations within the distance matrix to a
    # # dictionary.
    # for source in sourceList:
    #     sourceDict[source] = (0, D[0, :].index(source))
    # # adding sources to the graphs
    # for i in range(len(graphList)):
    #     graphList[i].add_node('source', value=sourceList[
    #                           i], index=sourceDict[sourceList[i]])

    # NOTE: if using node-by-node extension, then this needs to change.
    # processing matrix row by row, and extending the graph each time.
    for graph in graphList:
        counter = 0
        for i in range(1, len(row)):
            for j in range(i, len(col)):
                extend_digraph(graph, D, i, j, cost, counter)
                counter += 1
    return graphList


def extend_digraph(G, D, i, j, cost, counter):
    """ extends digraph node-by-node rather than row-by-row. i,j are the indices of the node that
    is the subject of the extension."""
    children_indices = find_children(i, j, D)
    if counter == 0:
        prev = 'source'
    else:
        prev = counter
    G.add_node(prev, value=D[i, j], index=(i, j))
    counter += 1
    if not children_indices:
        return G
    for child in children_indices:
        k, l = child
        current = counter
        G.add_node(current, value=D[k, l], index=(k, l))
        G.add_edge(prev, current, weight=cost(D[i, j], D[k, l]))
        counter += 1


def find_children(i, j, D):
    """finds the indices of valid successors"""
    row, col = D.shape
    # not reached boundaries of the distance matrix
    if D is None:
        return []
    if i + 1 < row and j + 1 < col:
        return [(i + 1, k) for k in range(j + 1, col)]
    else:
        return []


def findShortestPath(G):
    """ checks for the shortest path starting at indices 1...diff and ending at n-m...n"""
    pass
