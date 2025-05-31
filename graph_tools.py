
import networkx as nx
import random
from typing import Union

def prepare_graph(vertices, edges, sink_frac=0.2):
    """
    Transforms a graph into a valid Liquid Democracy Delegation Graph by performing the following operations:
    
    - Merges multiple (parallel) edges between the same nodes into a single edge, eliminating duplicates.
        Of the duplicate edges only one, random edge is kept.
    - Ensures that at least sinks % (default 20%) of nodes are sinks (outdegree 0)
        Edges are removed randomely until this condition is met
    - Normalizes the edge weights for each node such that the sum of outgoing edge weights equals 1.
    - Removes delegation cycles (terminal strongly connected components (SCCs))
        A terminal SCC is a strongly connected component that has no outgoing edges to nodes outside of
        the SCC. If such a component is found, one of its edges is removed at random.
        This process is repeated until no terminal SCCs remain.
    
    Parameters
    ----------
    vertices : iterable
        A list of the graph's vertices (nodes).
    edges : list of tuples
        A list of edges where each edge is a tuple:
        - (u, v, weight) 
        - (u, v) 
    sink_frac: float
        The percentage of nodes that should be sinks (outdegree 0). Default is 0.2 (20%).

    Returns
    -------
    networkx.DiGraph
    """
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
    for u, v, w in G.edges(data='weight'):
        if DG.has_edge(u, v):
            DG[u][v]['weight'] += w
        else :
            DG.add_edge(u, v, weight=w)

    # 3. If there are not a lot of sinks (less than 20% of nodes with outdegree 0), remove some edges
    while sum(DG.out_degree(n) == 0 for n in DG.nodes()) < sink_frac * len(DG.nodes):
        node = random.choice(list(DG.nodes()))
        if DG.out_degree(node) > 0:
            DG.remove_edges_from(list(DG.out_edges(node)))

    # 4. Normalize edge weights
    for node in DG.nodes():
        w_sum = sum(w for _, _, w in DG.out_edges(node, data='weight'))
        for u, v, w in DG.out_edges(node, data='weight'):
            DG.add_edge(u, v, weight=w / w_sum)

    # 5. Remove terminal SCCs (cliques with no sink)
    def remove_from_terminal_scc(graph):
        sccs = list(nx.strongly_connected_components(graph))
        for scc in sccs:
            if len(scc) == 1 and graph.has_edge(list(scc)[0], list(scc)[0]):
                # SCC is a self loop, which needs to be removed
                graph.remove_edge(list(scc)[0], list(scc)[0])
            terminal = True # assumes SCC is terminal unless an outgoing edge or sink is found
            for node in scc:
                # Search for sinks
                if graph.out_degree(node) == 0:
                    terminal = False
                    break
                
                # Search for outgoing edges
                for _, v in graph.out_edges(node):
                    if v not in scc:
                        terminal = False
                        break
                if not terminal:
                    break

            if terminal:
                # Terminal SCC found
                node = random.choice(list(scc))
                edge_to_remove = random.choice(list(graph.out_edges(node)))
                graph.remove_edge(*edge_to_remove)
                # Re-normalize the edge weights
                w_sum = sum(w for _, _, w in DG.out_edges(node, data='weight'))
                for u, v, w in DG.out_edges(node, data='weight'):
                    DG.add_edge(u, v, weight=w / w_sum)
                return True
        return False

    while remove_from_terminal_scc(DG):
        pass

    return DG

def nx_graph_to_dict(G: nx.DiGraph) -> dict:
    """
    Converts a NetworkX DiGraph to a dictionary representation like {src: {dst: weight, ...}, ...}.
    
    Parameters
    ----------
    G : networkx.DiGraph
        The directed graph to convert.

    Returns
    -------
    dict
        A dictionary where keys are nodes and values are dictionaries of neighbors and their weights.
    """
    return {src: {dst: data['weight'] for dst, data in G[src].items()} for src in G.nodes()}

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


def nx_graph_nodes_to_str(graph: Union[nx.Graph, nx.DiGraph]) -> Union[nx.Graph, nx.DiGraph]:
    """
    Converts the labels of nodes of a graph to strings by casting (str(node)).

    Parameters:
    - graph (networkx.Graph): The input graph with nodes to be converted.

    Returns:
    - networkx.Graph: A new graph with string labels for the nodes.
    """
    return nx.relabel_nodes(graph, {node: str(node) for node in graph.nodes()})

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