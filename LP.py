import numpy as np
from pulp import *

THIRD = 1/3

def resolve_delegations_LP(delegations: dict, nodes: list):
    # Initialize LP model
    model = LpProblem("DelegationResolution", LpMinimize)
    
    # Initialize LP variables
    lp_vars = {node: LpVariable(node) for node in nodes}
    
    # Add constraints for each node
    for node in nodes:
        incomings = delegations.get(node, {})
        model += (lp_vars[node] == 1 + sum(weight * lp_vars[src] for src, weight in incomings.items())), f"Constraint_{node}"
    
    # Identify sink nodes
    outgoing_nodes = {src for node in delegations for src, weight in delegations[node].items() if weight > 0}
    sink_nodes = [node for node in nodes if node not in outgoing_nodes]
    
    # Ensure no power is lost (the power of sink nodes has to equal the input power)
    model += sum(lp_vars[node] for node in sink_nodes) == len(nodes), "SinkNodesConstraint"

    print(model.constraints)
    
    model.solve()
    
    # Return the computed values
    return {node: value(var) for node, var in lp_vars.items()}, sink_nodes

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

 
def build_matrix(nodes, delegations, n, mode = "SE"):
    """
    Constructs a system of linear equations representing delegations in a liquid democracy 

    Parameters:
    - nodes (list): List of all nodes.
    - delegations (dict): A dictionary where keys are nodes, and values are 
      dictionaries mapping delegated nodes to weights.
    - n (int): The number of propagation steps.
    - mode (str): The mode to use for the simulation. Either "SE" (source effect) or "NSE" (no source effect).


    Returns:
    - A_eq (numpy.ndarray): Coefficient matrix.
    - b_eq (numpy.ndarray): Right-hand side vector.
    """

    # Number of variables (P value for each node at each step)
    num_vars = len(nodes) * (n + 1)

    # LHS and RHS vector (Ax = b)
    A_eq = []
    b_eq = []

    # Variable index mapping
    def idx(var, i):
        return len(nodes) * i + var
    
    # Invert the graph to get incoming delegations instead of outgoing ones
    delegations = invert_graph(delegations)

    # All nodes have a power of 1 at n = 0)
    for node in nodes:
        A_eq.append([1 if i == idx(node, 0) else 0 for i in range(num_vars)])
        b_eq.append(1)

    # Add constraints for each node for each propagation step
    for i in range(1, n + 1):
        for node in nodes:
            # Get delegations to the current node
            nodes_delegations = delegations.get(node, {})
            eq = [0] * num_vars
            eq[idx(node, i)] = 1
            for source, proportion in nodes_delegations.items():
                eq[idx(source, i - 1)] = -1 * proportion
            if mode == "SE":
                b_eq.append(1)
            elif mode == "NSE":
                b_eq.append(0)
            A_eq.append(eq)

    # Convert constraints to numpy arrays
    A_eq = np.array(A_eq)
    b_eq = np.array(b_eq)

    return (A_eq, b_eq)

def solve_linear_programming(A_eq, b_eq, num_nodes):
    """
    Solves the delegation system matrix using Linear Programming.

    Parameters:
    - A_eq (numpy.ndarray): Coefficient matrix.
    - b_eq (numpy.ndarray): Right-hand side vector.
    - num_nodes (int): Number of nodes in the delegation graph.

    Returns:
    - result.x (numpy.ndarray): Solution vector.
    """

    c = [-1] *  b_eq.size  # Minimize negative sum (equivalent to maximizing sum)
    
    res_LP = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method="highs")

    solution = res_LP.x

    print("Normalized LP results:")
    total = sum(solution[-num_nodes:])
    print_output = ""
    for i in range(num_nodes, 0, -1):
        print_output += f"{solution[-i] / total:.4f}, "
    print(print_output[:-1])

    return res_LP.x[-num_nodes:]

def solve_linear_equations(A_eq, b_eq, num_nodes):
    """
    Solves the delegation system as a system of linear equations.

    Parameters:
    - A_eq (numpy.ndarray): Coefficient matrix.
    - b_eq (numpy.ndarray): Right-hand side vector.
    - num_nodes (int): Number of nodes in the delegation graph.

    Returns:
    - x (numpy.ndarray): Solution vector.
    """
    try:
        solution = np.linalg.solve(A_eq, b_eq)
        
        print("Normalized LE results:")
        total = sum(solution[-num_nodes:])
        print_output = ""
        for i in range(num_nodes, 0, -1):
            print_output += f"{solution[-i] / total:.4f}, "
        print(print_output[:-1])

        return solution[-num_nodes:]
    except np.linalg.LinAlgError:
        print("Matrix is singular, no unique solution.")
        return None
    

def matrix_builder_and_solver(nodes, delegations, n, mode = "SE"):
    """
    Builds the delegation matrix and solves it using both Linear Programming 
    and Linear Equations methods.

    Parameters:
    - nodes (list): List of all nodes.
    - delegations (dict): Delegation dictionary with nodes as keys and their 
      delegations as values.
    - n (int): Number of propagations (not currently used in calculations).
    - mode (str): The mode to use for the simulation. Either "SE" (source effect) or "NSE" (no source effect).

    Returns:
    - (lp_solution, le_solution): Tuple containing the solutions from both methods.
    """
    A_eq, b_eq = build_matrix(nodes, delegations, n, mode)
    lp_solution = solve_linear_programming(A_eq, b_eq, len(nodes))
    le_solution = solve_linear_equations(A_eq, b_eq, len(nodes))
    
    return lp_solution, le_solution


