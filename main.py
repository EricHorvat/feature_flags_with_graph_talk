import logging
from pathlib import Path
from typing import List

import json
import os

import networkx as nx
from marshmallow import Schema, fields
from matplotlib import pyplot as plt
from networkx.drawing.nx_agraph import graphviz_layout

logger = logging.getLogger(__name__)

DEFAULT_FEATURE_FLAG_NAME_FILE = Path(os.getenv("FEATURE_FLAG_FILE",
                                                Path(__file__).parent / "data" / "feature_flags.json")
                                      )


class FeatureFlagSchema(Schema):
    descendants = fields.List(fields.String, required=True)
    subset = fields.Integer(required=True)


class FeatureFlag:
    # Licence types
    FREE = "free"
    TEAM = "team"
    ENTERPRISE = "enterprise"

    # Licence feature flags
    SAML = "SAML"
    PROTECTED_BRANCHES = "protected_branches"
    DRAFT_PR = "draft PR"
    PR = "PRs"

    def __init__(self):
        raise


def build_feature_dag(feature_flag_file_path=None):
    graph = nx.DiGraph()
    file_path = DEFAULT_FEATURE_FLAG_NAME_FILE if feature_flag_file_path is None else Path(feature_flag_file_path)
    processed_keys = set()
    keys = set()
    with file_path.open() as file:
        features_json: dict = json.loads(file.read())
        for key, list_value in features_json.items():
            graph.add_edges_from([(key, v) for v in list_value["descendants"]])
            graph.add_node(key, subset=list_value["subset"])
            keys.update(set(list_value["descendants"]))
            processed_keys.add(key)
    for key in keys.difference(processed_keys):
        graph.add_node(key, subset=6)
        processed_keys.add(key)

    return graph


def _test_feature_flags(feature_flag_file_path=None):
    graph = build_feature_dag(feature_flag_file_path)
    return nx.is_directed_acyclic_graph(graph)


def _show_feature_flags(graph: nx.DiGraph, mode='sorted'):
    """
    You need pygraphviz for this
    https://pygraphviz.github.io/documentation/stable/install.html
    """
    #plt.figure(figsize=(15, 15))
    if mode == 'sorted':
        pos = nx.multipartite_layout(graph)
        nx.draw(graph, pos, with_labels=True, arrows=True, node_color="#BA9DFB")
    else:
        pos = graphviz_layout(graph)
        nx.draw_networkx(graph, pos, arrows=True, node_color="#BA9DFB")
    plt.show()
    plt.clf()


def get_user_feature_flags(feature_flags: List[str], ignored_feature_flags: List[str], show=False, feature_flag_file_path=None):
    for elem in filter(lambda s: not isinstance(s, str), feature_flags + ignored_feature_flags):
        logger.warning(f"All features flags must be strings, {elem} passed and ignored")
    graph = build_feature_dag(feature_flag_file_path)
    graph.add_node("root", subset=0)
    graph.add_edges_from([("root", v) for v in filter(lambda s: isinstance(s, str), feature_flags)])
    graph.remove_nodes_from(set(nx.nodes(graph)).difference(nx.descendants(graph, "root")))
    graph.remove_nodes_from(ignored_feature_flags)
    if show:
        _show_feature_flags(graph, mode="unsorted")
    return set(graph.nodes())


if __name__ == '__main__':
    main_graph = build_feature_dag()
    print(_test_feature_flags())
    _show_feature_flags(main_graph)
    _show_feature_flags(main_graph, 'unsorted')
    print(get_user_feature_flags([FeatureFlag.FREE, FeatureFlag.DRAFT_PR], [FeatureFlag.PROTECTED_BRANCHES], True))
