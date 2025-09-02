import networkx as nx
import random
from typing import Union
import logger_creator

def prepare_graph(vertices, edges, sink_frac=0.2, seed=None):
    """
    Transforms a graph into a valid Liquid Democracy Delegation Graph by performing the following operations:
    
    - Merges multiple (parallel) edges between the same nodes into a single edge, eliminating duplicates.
        Of the duplicate edges only one, random edge is kept.
    - Ensures that at least sinks % (default 20%) of nodes are sinks (outdegree 0)
        Edges are removed randomly until this condition is met
    - Normalizes the edge weights for each node such that the sum of outgoing edge weights equals 1.
    - Removes closed delegation cycles (terminal strongly connected components (SCCs))
        A terminal SCC is a strongly connected component that has outgoing edges, but none of them to nodes outside of
        the SCC (so sinks are not terminal SCCS). If all such terminal SCCs are collapsed into a single 
        node called "lost". This process is repeated until no terminal SCCs remain.
    
    Parameters
    ----------
    vertices : iterable
        A list of the graph's vertices (nodes).
    edges : list of tuples
        A list of edges where each edge is a tuple or triple:
        - (u, v, weight) 
        - (u, v) 
    sink_frac: float
        The percentage of nodes that should be sinks (outdegree 0). Default is 0.2 (20%).

    Returns
    -------
    networkx.DiGraph
    """
    if seed is not None:
        random.seed(seed)

    # 1. Create initial graph
    G = nx.MultiDiGraph()
    G.add_nodes_from(vertices)
    for edge in edges:
        if len(edge) == 3:
            u, v, weight = edge
            G.add_edge(u, v, weight=weight)
        else:
            u, v = edge
            G.add_edge(u, v, weight=1)

    # 2. Merge multiple edges into one. The duplicated edges are discarded.
    DG = nx.DiGraph()
    DG.add_nodes_from(G.nodes())  

    for u, v, w in G.edges(data='weight'):
        if DG.has_edge(u, v):
            DG[u][v]['weight'] += w
        else :
            DG.add_edge(u, v, weight=w)

    # 3. If there are not a lot of sinks (less than 20% of nodes with outdegree 0), remove some edges
    while sum(DG.out_degree(n) == 0 for n in DG.nodes()) < sink_frac * len(G.nodes):
        node = random.choice(list(DG.nodes()))
        if DG.out_degree(node) > 0:
            DG.remove_edges_from(list(DG.out_edges(node)))

    # 4. Normalize edge weights
    for node in DG.nodes():
        w_sum = sum(w for _, _, w in DG.out_edges(node, data='weight'))
        for u, v, w in DG.out_edges(node, data='weight'):
            DG.add_edge(u, v, weight=w / w_sum)

    # 5. Remove closed delegation cycles (terminal strongly connected components (SCCs))
    initial_amount_of_nodes = len(DG.nodes())
    def collapse_all_terminal_sccs(graph, lost_node_name="cycle_sink_node"):
        # 1) find all SCCs
        sccs = list(nx.strongly_connected_components(graph))

        # 2) identify the terminal ones
        terminal_sccs = []
        for scc in sccs:
            # ignore sinks
            if any(graph.out_degree(n) == 0 for n in scc):
                continue
            # check whether there are any edges out of the scc
            # (checks if all outgoing edges are to nodes also in the SCC)
            if all(v in scc for u in scc for _, v in graph.out_edges(u)):
                terminal_sccs.append(scc)

        # 3) collapse each
        for scc in terminal_sccs:
            for node in scc:
                for u, _ in list(graph.in_edges(node)):
                    if u not in scc:
                        w = graph[u][node].get("weight", 1.0)
                        if graph.has_edge(u, lost_node_name):
                            graph[u][lost_node_name]["weight"] += w
                        else:
                            graph.add_edge(u, lost_node_name, weight=w)
                        graph.remove_edge(u, node)
            graph.remove_nodes_from(scc)

        # returns the amount of terminal SCCs that were collapsed
        return len(terminal_sccs)

    # Keep removing terminal SCCs until none are left
    amount_of_collapsed_sccs = collapse_all_terminal_sccs(DG)

    final_amount_of_nodes = len([n for n in DG.nodes() if n != "lost"])

    # Log results
    logger, handler = logger_creator.create_logger(name_prefix="prepare_graph")
    logger.info(f"Initially {initial_amount_of_nodes} nodes, after collapsing terminal SCCs "
                f"{final_amount_of_nodes} nodes remain. In total {amount_of_collapsed_sccs} terminal SCCs were collapsed.")
    logger.removeHandler(handler)
    handler.close()

    return DG

def nx_graph_to_dict(G: nx.DiGraph) -> dict:
    """
    Converts a NetworkX DiGraph to a dictionary representation like {src: {dst: weight, ...}, ...}.
    Defaults to weight=None if no weight is specified on an edge.

    Parameters
    ----------
    G : networkx.DiGraph
        The directed graph to convert.

    Returns
    -------
    dict
        A dictionary where keys are nodes and values are dictionaries of neighbors and their weights.
    """
    return {
        src: {
            dst: data.get('weight', None)
            for dst, data in G[src].items()
        }
        for src in G.nodes()
    }

def dict_to_nx_graph(graph_dict: dict) -> nx.DiGraph:
    """
    Converts a dictionary representation of a graph to a NetworkX DiGraph.

    Parameters:
    - graph_dict (dict): A dictionary where keys are nodes and values are dictionaries 
      of neighboring nodes and their weights.

    Returns:
    - networkx.DiGraph: A directed graph constructed from the input dictionary.
    """

    G = nx.DiGraph()

    for node, neighbors in graph_dict.items():
        for neighbor, weight in neighbors.items():
            G.add_edge(node, neighbor, weight=weight)

    return G

def invert_graph(graph):
    """
    Inverts a directed weighted graph by reversing the direction of all edges.

    Parameters:
    - graph (dict): A dictionary representing the original graph, where keys are nodes 
      and values are dictionaries mapping neighboring nodes to edge weights.

    Returns:
    - dict: A new dictionary representing the inverted graph, where all edges 
      have been reversed but retain their original weights.
    """
    inverted_graph = {}

    for node, neighbors in graph.items():
        for neighbor, weight in neighbors.items():
            if neighbor not in inverted_graph:
                inverted_graph[neighbor] = {}
            inverted_graph[neighbor][node] = weight  

    return inverted_graph