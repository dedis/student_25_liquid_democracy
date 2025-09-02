import pandas as pd
from jaal import Jaal

def visualize_delegation_graph(delegations: dict, powers: dict = None):
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
        powers (dict, optional): A dictionary mapping nodes to their power values. 

    Notes:
        - The powers return from an LP model need to be cleaned, so that non-sink nodes have a power of 0, otherwise
            they will be visualized as if held power (blue instead of gray).
        - The function will attempt to find an available port starting from 8050 until 8055.
        - The function assumes all nodes in the graph are present in the powers dict. If a node is missing from this dict, it will not be visualized.
        - If no powers dict is passed, the algorithm doesn't visualize any node who are not keys in the delegations dict
        - If no powers dict is passed, each node will be visualized as if it had no power (gray)
    """

    if not delegations: 
        print("No delegations to visualize.")
        return
    
    if not powers:
        powers = {node: 0.0 for node in delegations.keys()}

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
    while port < 8055:
        try:
            Jaal(edge_df, node_df).plot(directed=True,
                                        port=port,
                                        vis_opts={
                                            'interaction': {'hover': True},
                                            'node': {
                                                'color': "color", 
                                                'title': "power"
                                            }
                                        })
            
            break
        except Exception as e:
            print(e)
            port += 1

    print("Graph visualization failed because no ports were found or there was another error.")