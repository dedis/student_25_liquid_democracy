import numpy as np

WEIGHTS = [(i + 1) / 10 for i in range(1, 10)]

def get_random_delegation_weights(n: int) -> list:
    """
    Generates up to `n` random weights from the set of {0.1, 0.2, ..., 0.9} such that they sum to exactly 1.0.

    Parameters:
    - n (int): Maximum number of weights to generate.

    Returns:
    - list[float]: A list of up to `n` values that sum to 1.0.

    Notes:
        - If `n <= 0`, an empty list is returned.
        - The algorithm may find less than 'n' weights, if e.g. n = 2, the algorithm may choose 1.0 as weight and only return [1.0]
        - The algorithm ensures no negative values
    """
    if n <= 0: return []

    diff = 1
    weights = []
    for i in range(n-1):
        for _ in range(11):
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

def create_delegation_graph(num_nodes: int, seed: int = None):
    """
    Generates a random delegation graph with fractional delegations, avoiding closed cycles and ensuring connectivity to a sink.

    Each node may delegate its vote fractionally to up to 3 other nodes. Delegations are assigned randomly such that
    the sum of weights from any node equals 1.0. The graph is guaranteed to be free of closed delegation cycles.

    Parameters:
    - num_nodes (int): The number of nodes (voters) in the graph.
    - seed (int, optional): A random seed for reproducibility.

    Returns:
    - delegations (dict[int, dict[int, float]]): A nested dictionary representing the delegation graph.
      Outer keys are source nodes; inner keys are target nodes with associated delegation weights.
    - nodes (list[int]): A list of all nodes

    Notes:
    - Delegation weights are all multiples of 0.1
    """

    np.random.seed(seed)

    nodes = list(range(num_nodes))
    delegations = {}
    for i in range(num_nodes):
        node = i     
        # Choose how many delegations this node shall have
        num_delegations = np.random.randint(0, min(3, i) + 1)
        if num_delegations > 0:
            delegation_weights = get_random_delegation_weights(num_delegations)

            delegates = np.random.choice(nodes, num_delegations, replace=False)
            # Sorting assures that if the node delegates to itself, this delegation is first in the list.
            delegates = sorted(delegates, reverse=True) 

            for j in range(len(delegation_weights)):
                delegate = delegates[j]

                # Avoids self delegations of any weight
                # This causes the outdgoing power of this node to no longer be 1, but that will be fixed later on
                if (delegate == node):
                        continue
                else:
                    # Add the delegation to the dictionary, initializing if necessary
                    delegations.setdefault(node, {}).setdefault(delegate, 0)
                    delegations[node][delegate] += delegation_weights[j]
                    if not is_connected_to_sink(delegations, node):
                        # If the delegation graph is not connected to a sink, remove the delegation
                        # This causes the outdgoing power of this node to no longer be 1, but that will be fixed later on
                        delegations[node][delegate] -= delegation_weights[j]
                        if delegations[node][delegate] <= 0:
                            del delegations[node][delegate]
                
            # Ensure node has outgoing delegations summing to 1.0
            if node in delegations and sum(delegations[node].values()) < 1.0:
                # If the node has outgong delegations, distribute the remaining weight evenly among the existing delegations
                remaining_weight = 1.0 - sum(delegations[node].values())
                for delegate in delegations[node]:
                    delegations[node][delegate] += remaining_weight / len(delegations[node])
                
  
    return delegations, nodes