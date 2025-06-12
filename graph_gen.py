import numpy as np

WEIGHTS = [(i + 1) / 10 for i in range(1, 10)]

def get_random_delegation_weights(n: int) -> list:
    """
    Generates at most `n` random weights from the set of {0.1, 0.2, ..., 0.9} such that they sum to exactly 1.0.

    Parameters:
    - n (int): The number of weights to generate.

    Returns:
    - list[float]: A list of `n` values that sum to 1.0.

    Notes:
        - If `n == 0`, an empty list is returned.
        - The algorithm may find less than 'n' weights, if e.g. n = 2, the algorithm may choose 1.0 as weight and only return [1.0]
        - The algorithm ensures no negative values
    """
    if n == 0: return []

    diff = 1
    weights = []
    for i in range(n-1):
        for j in range(11):
            # Tries 10 times to find a valid weight. If this is not possible the algorithm gives up
            choice = np.random.choice(WEIGHTS)
            if diff - choice > 0:
                weights += [choice]
                diff -= weights[-1]
                break
    
    # If we have not used all the weights, add the last one
    if diff > 0:
        weights += [round(diff, 1)]

    return weights

def is_connected_to_sink(delegations, start_node):
    visited = set()

    def dfs(node):
        if node in visited:
            return False 
        
        visited.add(node)

        # A sink is a node with no outgoing edges 
        if node not in delegations or not delegations[node]:  
            return True  

        # Recur for all outgoing connections
        return any(dfs(neighbor) for neighbor in delegations[node])

    return dfs(start_node)

def create_delegation_graph(num_nodes: int, num_loops: int, seed: int = None):
    """
    Generates a random delegation graph with a specified number of nodes and loops.

    Parameters
    ----------
    num_nodes : int
        Number of nodes (voters) in the graph.
    num_loops : int
        Number of loops (cyclical delegations) to add after initial graph construction.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    delegations : dict
        A dictionary representing the delegation graph. Keys are node identifiers (str),
        and values are dictionaries mapping delegate nodes to delegation weights.
    nodes : list of str
        List of node identifiers used in the graph.

    Notes
    -----
    - Each node will have between 0 and 3 delegations to random other delegates
    - Self-delegations are possible if they do not violate the rules for a well-formed delegation graph
    - Loops are only added if they do not disconnect the graph from the sinks.
    """

    np.random.seed(seed)

    nodes = []
    delegations = {}
    for i in range(num_nodes):
        node = str(i)
        nodes += [node]
        # Choose how many delegations this node shall have
        num_delegations = np.random.randint(0, min(3, i) + 1)
        if num_delegations > 0:
            delegation_weights = get_random_delegation_weights(num_delegations)

            delegates = np.random.choice(nodes, num_delegations, replace=False)
            # Sorting assures that if the node delegates to itself, this delegation is first in the list.
            delegates = sorted(delegates, reverse=True) 

            for j in range(len(delegation_weights)):
                delegate = delegates[j]

                # Avoids delegations of N -1-> N, which are not allowed (since N is not voting and voting at the same time)
                if (delegate == node) and ((delegation_weights[j] == 1) or delegations.get(node, {}).get(node, 0) + delegation_weights[j] == 1):
                    # If the only delegate is itself, turn this node into a sink by just not adding the delegation 
                    if len(delegates) == 1:
                        break 
                    # Else remove the delegation, and add the weight to the next delegate's weight
                    else:
                        delegation_weights[j + 1] +=  delegation_weights[j] 
                        continue

                else:
                    delegations.setdefault(str(node), {}).setdefault(str(delegate), 0)
                    delegations[node][delegate] += delegation_weights[j]

    for i in range(num_loops):
        
        # Try to find a non-sink node with which to create a loop
        node = None
        for j in range(len(nodes)):
            node = np.random.choice(nodes)
            if node not in delegations or len(delegations[node]) == 0:
                node = None
            else:
                break

        for j, delegate in enumerate(delegations.get(node, {})):
            # Try to create a loop between this node and the selected delegate

            # #If delegate is a sink
            if delegate not in delegations or len(delegations[delegate]) == 0:
                # Add the loop
                delegations[delegate] = {str(node): 1}

                # Check that we did not create an illegal cycle
                if not is_connected_to_sink(delegations, node):
                    # Remove the loop
                    del delegations[delegate]
                    continue
            # Delegate is not a sink
            else:

                # Choose any weight from the set of weights, except 1
                # Adding a new delegation with weight 1 might create a cycle
                new_delegation_weight = np.random.choice([weight for weight in WEIGHTS if weight not in [1]])

                # Free up weight from the other delegations
                for k, v in delegations[delegate].items():
                        delegations[delegate][k] = (1 - new_delegation_weight) * v

                # Add this weight directed toward the node, to create a loop 
                delegations[delegate].setdefault(str(node), 0)
                delegations[delegate][node] += new_delegation_weight

                break

    return delegations, nodes