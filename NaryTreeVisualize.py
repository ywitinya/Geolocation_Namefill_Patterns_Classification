import networkx as nx
import seaborn as sns
import matplotlib.pyplot as plt
from collections import defaultdict
import pandas as pd
import argparse
from NaryTree import (NaryTree, MatchNode)
from difflib import get_close_matches
import re
from geoip_database import get_iso_country
# --- Build graph from tree ---

def build_graph(node: MatchNode, graph: nx.DiGraph, parent_label=None):
    label = f"{node.label}"
    if node.values:
        label += f"\n({len(node.values)} values)"
    
    graph.add_node(label)

    if parent_label:
        graph.add_edge(parent_label, label)

    for child in node.children.values():
        build_graph(child, graph, label)

def draw_tree(nray_tree: NaryTree):
    G = nx.DiGraph()
    build_graph(nray_tree.root, G)
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(14, 10))
    nx.draw(G, pos, with_labels=True, node_size=2500, font_size=8, node_color='lightblue', edge_color='gray')
    plt.title("NaryTree DNS Pattern Visualization")
    plt.tight_layout()
    plt.show()

def generate_mermaid_tree(node, parent_label=None, lines=None, node_id=0, aggregated=False):
    if lines is None:
        lines = ["flowchart TD"]
    node_values = list(node.values)
    
    if aggregated and node_values:
        examples = ', '.join(node_values[:3])
        node_label = f"{node.label} .i.e. {examples}".replace('"', "'")  # Escape quotes
    else:
        node_label = f"{node.label}".replace('"', "'")

    current_id = f"n{node_id}"
    lines.append(f'{current_id}["{node_label}"]')

    if parent_label is not None:
        lines.append(f"{parent_label} --> {current_id}")

    this_id = current_id
    child_id = node_id + 1

    for child in node.children.values():
        lines, child_id = generate_mermaid_tree(child, this_id, lines, child_id, aggregated=True)

    return lines, child_id

def plot_tree_metrics(metrics_dict):
    df = pd.DataFrame(metrics_dict).T.reset_index()
    df= df.rename(columns={"index": "etldp1"})
    melted_df = df.melt(id_vars="etldp1", var_name="Metric", 
                        value_vars=["branching_to_leaf_ratio", "average_out_degree"])

    plt.figure(figsize=(10, 6))
    sns.barplot(data=melted_df, x="etldp1", y="value", hue="Metric")
    plt.title("Tree Complexity Metrics Across etldp1")
    plt.xlabel("eTLD+1")
    plt.ylabel("Metric Value")
    plt.xticks(rotation=45)
    plt.show()
    return df


# --- Main program ---

def main():
    # lines, _ = generate_mermaid_tree(trees['comcast.net'].root)
    # mermaid_script = "\n".join(lines)

    # # write to file
    # with open("dns_tree.mmd", "w") as f:
    #     f.write(mermaid_script)
    
    # draw_tree(trees['amazonaws.com'])
    pass

if __name__ == "__main__":
    main()
