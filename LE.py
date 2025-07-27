import numpy as np
from typing import List, Tuple
from scipy.sparse import csc_array
from scipy.sparse.linalg import spsolve

def get_node_to_int_map(nodes: list) -> dict:
    return {node: i for i, node in enumerate(nodes)}

def set_up(delegations: dict, nodes: list):

    n = len(nodes)
    node_to_int = get_node_to_int_map(nodes)

    # Finds sink nodes, since they get treated different when building the matrix
    outgoing_nodes = {src for node in delegations for src, weight in delegations[node].items() if weight > 0}
    sink_nodes = [node for node in nodes if node not in outgoing_nodes]

    # We will assemble A in coordinate format: lists of (row, col, data)
    rows = []
    cols = []
    data = []

    for v in nodes:
        v_int = node_to_int[v]
        # Diagonal entry: 1 * p_v
        rows.append(v_int)
        cols.append(v_int)
        data.append(1.0)

        # Subtract incoming weights:  -w_{uv} * p_u
        for u, w in delegations.get(v, {}).items():
            u_int = node_to_int[u]
            rows.append(v_int)
            cols.append(u_int)
            data.append(-w)

    # Create sparse matrix A in CSC format:
    A = csc_array((data, (rows, cols)), shape=(n, n))

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

