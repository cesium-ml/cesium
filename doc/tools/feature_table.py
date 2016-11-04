from tabulate import tabulate
import re
from cesium.features.graphs import (feature_categories, dask_feature_graph,
                                    extra_feature_docs)


def feature_graph_to_rst_table(graph, category_name):
    """Convert feature graph to Sphinx-compatible ReST table."""
    header = [category_name, 'Description']
    table = []
    for feature_name in sorted(
            graph, key=lambda s: [int(t) if t.isdigit() else t
                                  for t in re.split('(\d+)', s)]):
        description = (extra_feature_docs[feature_name] if feature_name in
                       extra_feature_docs else
                       ' '.join([e.strip() for e in
                                 graph[feature_name][0].__doc__.split('\n\n')[0]
                                 .strip().split('\n')]))
        table.append([feature_name, description])

    return tabulate(table, headers=header, tablefmt='rst')


def write_feature_tables(fname):
    with open(fname, 'w') as f:
        f.write('==============================\n'
                'Cesium Features - By Category\n'
                '==============================\n\n')

        dfg = dask_feature_graph

        for category in feature_categories:
            graph = {feature: dfg[feature]
                         for feature in feature_categories[category]}

            f.write(feature_graph_to_rst_table(graph, category) + '\n\n')
