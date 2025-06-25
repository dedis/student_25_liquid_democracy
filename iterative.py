import sys, os
sys.path.append(os.path.abspath("/Users/DavidHolzwarth/Uni/EPFL/bachelors-thesis"))

import logger_creator
import time 

def iterate_delegations(delegations: dict, nodes: list, cutoff: float = 0.001) -> dict:
    """
    Iteratively updates node values based on incoming delegations.

    Args:
        delegations (dict): A dictionary mapping nodes to their incoming delegations. Keys are node names and values 
                            are dictionaries mapping source nodes to delegation weights. 
                            Example (B delegates 0.5 to A and 0.5 to C, and A delegates 1.0 to C):
                            {
                                "A": {"B": 0.5},
                                "C": {"A": 1.0, "B": 0.5}
                            }
        nodes (list): A list of all nodes in the delegation graph.
        cutoff (float): The threshold for stopping early if total change is strictly below this value.

    Returns:
        - dict: A mapping of nodes to their resolved voting power after solving the LP.
    
    Notes:
        - If the delegations are not resolvable because there is a clique with no sink, the function will not terminate.
    """
    # Initialize node values
    values = {node: 1.0 for node in nodes}

    count = 0
    
    while True:

        temp_values = values.copy()  # Store previous iteration values
        total_change = 0.0
        
        for node, incoming_delegations in delegations.items():
            incoming_delegations = delegations[node]

            for src, weight in incoming_delegations.items():
                values[node] += weight * temp_values[src]
                values[src] -= weight * temp_values[src]
                total_change += weight * temp_values[src]
        
        count += 1
        if total_change < cutoff:

            logger, handler = logger_creator.create_logger(name_prefix="iterative")
            logger.info(f"Iterated {count} times ({len(nodes)} nodes)")
            logger.removeHandler(handler)
            handler.close()
            
            return values
        