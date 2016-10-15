from tabulate import tabulate
import re
from cesium.features.graphs import feature_categories, dask_feature_graph


def feature_graph_to_rst_table(graph, category_name):
    """Convert feature graph to Sphinx-compatible ReST table."""
    header = [category_name, 'Description']
    table = []
    for feature_name in sorted(
            graph.keys(), key=lambda s: [int(t) if t.isdigit() else t
                                         for t in re.split('(\d+)', s)]):
        table.append([feature_name, graph[feature_name][0].__doc__.split('\n')[0]])

    return tabulate(table, headers=header, tablefmt='rst')


def write_feature_tables(fname):
    with open(fname, 'w') as f:
        f.write('================\n'
                'Cesium Features\n'
                '================\n\n')

        dfg = dask_feature_graph

        for category in ['cadence', 'general', 'lomb_scargle']:
            graph = {feature: dfg[feature]
                         for feature in feature_categories[category]}

            f.write(feature_graph_to_rst_table(graph, category) + '\n')
