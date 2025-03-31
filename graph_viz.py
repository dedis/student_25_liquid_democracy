import pandas as pd
from jaal import Jaal

def visualize_delegation_graph(delegations: dict, powers: dict):
    node_df = pd.DataFrame({
        "id": powers.keys(),
         "power": powers.values()
    })

    node_df["sink?"] = node_df["power"].astype(float) > 0
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
