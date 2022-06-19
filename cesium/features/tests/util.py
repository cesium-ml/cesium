import dask
import numpy as np

from cesium.features import generate_dask_graph


def generate_features(t, m, e, features_to_use):
    """Utility function that generates features from a dask DAG."""
    graph = generate_dask_graph(t, m, e)
    values = dask.get(graph, features_to_use)
    return dict(zip(features_to_use, values))


def irregular_random(seed=0, size=50):
    """Generate random test data at irregularly-sampled times."""
    state = np.random.RandomState(seed)
    times = np.sort(state.uniform(0, 10, size))
    values = state.normal(1, 1, size)
    errors = state.exponential(0.1, size)
    return times, values, errors


def regular_periodic(freqs, amplitudes, phase, size=501):
    """Generate periodic test data sampled at regular intervals: superposition
    of multiple sine waves, each with multiple harmonics.
    """
    times = np.linspace(0, 2, size)
    values = np.zeros(size)
    for (i, j), amplitude in np.ndenumerate(amplitudes):
        values += amplitude * np.sin(2 * np.pi * times * freqs[i] * (j + 1) + phase)
    errors = 1e-4 * np.ones(size)
    return times, values, errors


def irregular_periodic(freqs, amplitudes, phase, seed=0, size=501):
    """Generate periodic test data sampled at randomly-spaced intervals:
    superposition of multiple sine waves, each with multiple harmonics.
    """
    state = np.random.RandomState(seed)
    times = np.sort(state.uniform(0, 2, size))
    values = np.zeros(size)
    for i in range(freqs.shape[0]):
        for j in range(amplitudes.shape[1]):
            values += amplitudes[i, j] * np.sin(
                2 * np.pi * times * freqs[i] * (j + 1) + phase
            )
    errors = state.exponential(1e-2, size)
    return times, values, errors
