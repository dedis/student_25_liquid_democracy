import numpy as np
from typing import List, Tuple
from scipy.sparse import csc_array
from scipy.sparse.linalg import spsolve



def get_node_to_int_map(nodes: list) -> dict:
    return {node: i for i, node in enumerate(nodes)}

def set_up(delegations: dict, nodes: list):

    # Map each node to a int key
    node_to_int_map = get_node_to_int_map(nodes)

    # Finds sink nodes, since they get treated different when building the matrix
    outgoing_nodes = {src for node in delegations for src, weight in delegations[node].items() if weight > 0}
    sink_nodes = [node for node in nodes if node not in outgoing_nodes]

    rows = []

    for node in nodes:
        row = [0] * len(nodes)

        row[node_to_int_map[node]] = 1

        for incoming in delegations.get(node, {}):
            row[node_to_int_map[incoming]] = (-1 * delegations[node][incoming]) + row[node_to_int_map[incoming]]

        rows.append(row)

    A = np.array(rows)
    b = np.array([1] * len(nodes))

    return A, b, sink_nodes

def solve(A, b, sinks=None):

    # An empty graph would break the LE solver
    if A.size == 0:
        return {}, []
    
    try:
        #x = np.linalg.solve(A, b)
        x = spsolve(A, b)
    except np.linalg.LinAlgError as e:
        raise ValueError(f"Linear system is unsolvable: {e}")
    
    return x

def resolve_delegations(delegations: dict, nodes: List[str]) -> Tuple[dict, list]:

    A, b, sink_nodes = set_up(delegations, nodes)
    x = solve(A, b)

    node_to_int_map = get_node_to_int_map(nodes)

    # Create a dictionary to store the resolved powers
    powers = {node: (float(x[node_to_int_map[node]]) if node in sink_nodes else 0.0) for node in nodes}

    return powers, sink_nodes

