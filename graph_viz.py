import pandas as pd
from jaal import Jaal

def visualize_delegation_graph(delegations: dict, powers: dict):
    """
    Visualizes a delegation graph using the Jaal library.
    Args:
        delegations (dict): A dictionary mapping nodes to their incoming delegations. Keys are node names and values 
                            are dictionaries mapping source nodes to delegation weights. 
                            Example (B delegates 0.5 to A and 0.5 to C, and A delegates 1.0 to C):
                            {
                                "A": {"B": 0.5},
                                "C": {"A": 1.0, "B": 0.5}
                            }
        powers (dict): A dictionary mapping nodes to their power values. 

    Notes:
        - The powers return from an LP model need to be cleaned, so that non-sink nodes have a power of 0, otherwise
            they will be visualized as if held power (blue instead of gray node color).
        - The function will attempt to find an available port starting from 8050.
        - The graph is directed, with nodes colored based on whether they are sinks (blue) or not (gray).

    """

    node_df = pd.DataFrame({
        "id": powers.keys(),
         "power": powers.values()
    })

    node_df["sink?"] = node_df["power"].astype(float) > 0.0
    node_df["color"] = node_df["sink?"].map({True: "blue", False: "gray"})

    
    edges = []
    for node, neighbors in delegations.items():
        for neighbor, weight in neighbors.items():
            edges.append((node, neighbor, weight))

    edge_df = pd.DataFrame(edges, columns=["from", "to", "label"])
    edge_df["label"] = edge_df["label"].astype(str)

    port = 8050
    while True:
        try:
            Jaal(edge_df, node_df).plot(directed=True,
                                        port=port,
                                        vis_opts={
                                            'interaction': {'hover': True},
                                            'node': {
                                                'color': 'color', 
                                                'title': 'power'
                                            }
                                        })
            
            break
        except:
            port += 1

def clean_powers(powers, sinks):
    """
    NO LONGER NECESSARY
    Cleans the powers dictionary so that non-sink nodes have a power of 0.
    
    Args:
        powers (dict): A dictionary mapping nodes to their power values.
        sinks (list): A list of sink nodes.

    Returns:
        dict: A cleaned dictionary with non-sink nodes set to 0.
    """
    for node in powers.keys():
        if node not in sinks:
            powers[node] = 0.0
    return powers