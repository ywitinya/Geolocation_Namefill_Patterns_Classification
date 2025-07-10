from collections import defaultdict


"""
Tree Complexity Analyzer:
Measures:
1. Leaf Count number of terminal nodes
2. Branching-to-Leaf Ratio total internal branches divided by number of leaves
3. Average-outward-metric 
"""

def count_leaf_nodes(tree):
    """Count the number of leaf nodes in the tree."""
    def dfs(node):
        if not node.children:
            return 1
        return sum(dfs(child) for child in node.children.values())
    return dfs(tree.root)

def count_total_nodes(tree):
    """Count total number of nodes in the tree."""
    def dfs(node):
        count = 1
        for child in node.children.values():
            count += dfs(child)
        return count
    return dfs(tree.root)

def count_internal_nodes(tree):
    """Count internal nodes (nodes with at least one child)."""
    def dfs(node):
        if not node.children:
            return 0
        return 1 + sum(dfs(child) for child in node.children.values())
    return dfs(tree.root)

def total_branches(tree):
    """Count all branch edges (total children across internal nodes)."""
    def dfs(node):
        count = len(node.children)
        for child in node.children.values():
            count += dfs(child)
        return count
    return dfs(tree.root)

def branching_to_leaf_ratio(tree):
    """Compute ratio of total branches to number of leaves."""
    leaves = count_leaf_nodes(tree)
    branches = total_branches(tree)
    return leaves/ branches if leaves else 0

def average_out_degree(tree):
    """Compute the number of outward branches at each internal node and return the average"""
    total_branches = 0
    total_internal_nodes = 0

    def dfs(node):
        nonlocal total_branches, total_internal_nodes
        if node.children:
            total_branches += len(node.children)
            total_internal_nodes += 1
            for child in node.children.values():
                dfs(child)

    dfs(tree.root)

    return total_branches / total_internal_nodes if total_internal_nodes > 0 else 0


def analyze_tree_complexity(tree):
    """Return a dictionary of all relevant complexity metrics."""
    return {
        # "total_nodes": count_total_nodes(tree),
        # "leaf_count": count_leaf_nodes(tree),
        # "internal_node_count": count_internal_nodes(tree),
        # "total_branches": total_branches(tree),
        "branching_to_leaf_ratio": branching_to_leaf_ratio(tree),
        "average_out_degree": average_out_degree(tree)
    }
