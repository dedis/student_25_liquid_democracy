
import networkx as nx
import random

def prepare_graph(vertices, edges):
    """
    Transforms a graph into a valid Liquid Democracy Delegation Graph by performing the following operations:
    
    - Merges multiple (parallel) edges between the same nodes into a single edge, eliminating duplicates.
        Of the duplicate edges only one, random edge is kept.
    - Ensures that at least 20% of nodes are sinks (outdegree 0)
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
    if sum(DG.out_degree(n) == 0 for n in DG.nodes()) < 0.2 * len(DG.nodes):
        node = random.choice(DG.nodes())
        if len(DG.out_degree(node)) > 0:
            DG.remove_edge(*list(DG.out_edges(node)))

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
