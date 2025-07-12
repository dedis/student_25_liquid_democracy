import logger_creator
import numpy as np
from datetime import datetime
from pulp import *

# These two are necessary, since PuLP needs variables to be strings, but they may be input as integers or other types
# Eg. a node being called either 1 or '1'
def get_node_to_str_map(nodes: list) -> dict:
    return {node: str(node) for node in nodes}

def get_str_to_node_map(nodes: list) -> dict:
    return {str(node): node for node in nodes}

def set_up(delegations: dict, nodes: list):
    """
    nodes need to be strings
    """

    node_to_str = get_node_to_str_map(nodes)

    # Initialize LP model
    model = LpProblem("DelegationResolution", LpMinimize)
    
    # Initialize LP variables
    lp_vars = {node: LpVariable(node_to_str[node]) for node in nodes}

    # Identify sink and non-sink nodes. Outgoing nodes are those that have delegations going out of them
    outgoing_nodes = {src for node in delegations for src, weight in delegations[node].items() if weight > 0}
    sink_nodes = [node for node in nodes if node not in outgoing_nodes]
    
    # Add constraints for each node
    for node in nodes:
        incomings = delegations.get(node, {})
        model += (lp_vars[node] == 1 + sum(weight * lp_vars[src] for src, weight in incomings.items())), f"Constraint_{node_to_str[node]}"

    return model, sink_nodes


def solve(model, sink_nodes=None):

    model.solve(PULP_CBC_CMD(msg=0, options=["primalT=5e-3", "dualT=5e-3"]))

def resolve_delegations(delegations: dict, nodes: List[str]) -> Tuple[dict, list]:
    """
    Resolves delegations in a weighted delegation graph using a LP model.

    This function constructs an LP problem where each node receives voting power from incoming delegations. 
    The objective is to ensure that all delegation flows are properly accounted for, including cycles, 
    while sink nodes absorb the total delegated power.

    Args:
        delegations (dict): A dictionary mapping nodes to their incoming delegations. Keys are node names and values 
                            are dictionaries mapping source nodes to delegation weights. 
                            Example (B delegates 0.5 to A and 0.5 to C, and A delegates 1.0 to C):
                            {
                                "A": {"B": 0.5},
                                "C": {"A": 1.0, "B": 0.5}
                            }
        nodes (list): A list of all nodes in the delegation graph. Nodes must be strings.

    Returns:
       tuple:
            - dict: A mapping of nodes to their resolved voting power after solving the LP.
            - list: A list of sink nodes (nodes without outgoing delegations).

    Notes:
        - A function "inverse_graph" may be used to invert the delegation graph, if it is currently mapping keys to outgoing
            delegations.
        - The function returns a list of sinks, since the resolved voting power of non-sinks is not meaningful, 
            and should thus be ignored when treating the output
        - Sink nodes (nodes without outgoing delegations) must collectively hold the total power.
    """
    model, sink_nodes = set_up(delegations, nodes)

    solve(model)

    str_to_node_map = get_str_to_node_map(nodes)

    # Return the computed values
    if (model.status == 1):
        return {
            str_to_node_map[var.name]: (value(var) if str_to_node_map[var.name] in sink_nodes else 0.0)
            for var in model.variables()
            if var.name != "__dummy" # Exclude the dummy variable created by PuLP
        }, sink_nodes
    else:
        raise Exception(f"LP model is {constants.LpStatus[model.status]}. {model}")
