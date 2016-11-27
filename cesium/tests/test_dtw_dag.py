import networkx as nx
import numpy as np
from cesium import dtw_dag as dtw
from math import sqrt


def test_cost_matrix():
    v1 = np.array([1, 2, 8, 6, 8]).reshape(1, 5)
    v2 = np.array([1, 2, 9, 3, 3, 5, 9]).reshape(1, 7)
    D = dtw.getDistanceMatrix(v1, v2)
    npt.assert_array_equal(D.shape, (5, 7))
    ans = np.array([[0, 1, 8, 2, 2, 4, 8],
                    [-1, 0, 7, 1, 1, 3, 7],
                    [-7, -6, 1, -5, -5, -3, 1],
                    [-5, -4, 3, -3, -3, -1, 3],
                    [-7, -6, 1, -5, -5, -3, 1]])
    npt.assert_almost_equal(D, ans)


def test_computation():
    dmat = np.array([[0, 1, 8, 2, 2, 4, 8],
                     [-1, 0, 7, 1, 1, 3, 7],
                     [-7, -6, 1, -5, -5, -3, 1],
                     [-5, -4, 3, -3, -3, -1, 3],
                     [-7, -6, 1, -5, -5, -3, 1]])
    G = dtw.constructGraph(dmat)
    result = dtw.findShortestPath(G)
    # answer computed in linked paper.
    npt.assert_equal(result, sqrt(3))


def test_graph_construction():
    pass


def test_distance_metrics():
    pass


# TODO: rewrite.

def test_find_children():
    G = nx.DiGraph()
    dmat = np.array([[0, 1, 8, 2, 2, 4, 8],
                     [-1, 0, 7, 1, 1, 3, 7],
                     [-7, -6, 1, -5, -5, -3, 1],
                     [-5, -4, 3, -3, -3, -1, 3],
                     [-7, -6, 1, -5, -5, -3, 1]])

    sources = dmat[0, :2]
    first_successors = dtw.find_children(0, 0, 7)
    second_successors = dtw.find_children(0, 1, 7)
    npt.assert_equal(len(first_successors), 6)
    npt.assert_equal(len(second_successors), 5)
    true_first = [(0, 0), (0, 7), (0, 1), (0, 1), (0, 3), (0, 7)]
    true_second = [(1, 7), (1, 1), (1, 1), (1, 3), (1, 7)]
    npt.assert_array_equal(first_successors, true_first)
    npt.assert_array_equal(second_successors, true_second)
