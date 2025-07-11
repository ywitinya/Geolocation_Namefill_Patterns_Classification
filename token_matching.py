import argparse
import sys
import re
import pandas as pd
import gzip
import json
from collections import defaultdict, deque
from difflib import get_close_matches


from NaryTree import (NaryTree, MatchNode)
from geoip_database import get_iso_country
import load_geo_database as geo
from NaryTreeVisualize import (generate_mermaid_tree, draw_tree, plot_tree_metrics)
from NaryTreeComplexity import analyze_tree_complexity


MATCHERS = ["GEO-names", "UN-locode", "UN-subdiv", "directional", "GEO-classification"]

def normalize_namefill_pattern(raw_pattern: str) -> str:
    def replacer(match):
        content = match.group(1)
        if re.search(r'ip\[\d+\]', content):
            ip_index = re.search(r'ip\[(\d+)\]', content).group(1)
            return f"{{ip{ip_index}}}"
        return f"seq:{content}"

    pattern = re.search(r'f"(.*?)"', raw_pattern)
    if pattern:
        raw_fqdn = pattern.group(1)
        fqdn = re.sub(r'{([^}]+)}', replacer, raw_fqdn)
        return fqdn
    return None

def collect_tokens_by_level(tree_root):
    tokens_by_depth = defaultdict(set)
    queue = deque([(tree_root, 0)])
    while queue:
        node, depth = queue.popleft()
        for label, child in node.children.items():
            tokens_by_depth[depth].add(label)
            queue.append((child, depth + 1))
    return tokens_by_depth

def match_geonames(tokens_by_depth, geo_names):
    reverse_index = {}
    for entry in geo_names:
        reverse_index['name'] = entry['ascii']
        if entry['alternates']:
            for alt in entry['alternates']:
                reverse_index[alt] = entry['name']

    matched = defaultdict(set)
    for depth, tokens in tokens_by_depth.items():
        for token in tokens:
            stripped = token.strip('.-')
            if stripped in reverse_index:
                matched[depth].add((stripped, reverse_index[stripped]))
    return matched

def match_terms(tokens_by_depth, term_set, label):
    matched = defaultdict(set)
    for depth, tokens in tokens_by_depth.items():
        for token in tokens:
            stripped = token.strip('.-')
            if stripped in term_set:
                matched[depth].add((stripped, stripped))
    return matched

def build_modified_tree(original_tree, matches_by_depth, match_type, aggregated=False):
    new_tree = NaryTree()

    def dfs(orig_node, new_node, depth):
        for label, child in orig_node.children.items():
            token_key = label.strip('.-')

            if depth in matches_by_depth and any(token_key == m[0] for m in matches_by_depth[depth]):
                if aggregated and match_type not in MATCHERS[3:]:    
                    new_label = f"{match_type}"
                else:
                    new_label = f"{match_type}:{label}"
            else:
                new_label = label

            if new_label not in new_node.children:
                new_node.children[new_label] = MatchNode(new_label)
            if new_label != label:
                if label.startswith(".") or label.startswith("-"):
                    new_node.children[new_label].values.add(label)
            new_node.children[new_label].values.update(child.values)
            dfs(child, new_node.children[new_label], depth + 1)

    dfs(original_tree.root, new_tree.root, 0)
    return new_tree


def combine_trees(target_tree, source_tree):
    def dfs(t_node, s_node):
        for label, s_child in s_node.children.items():
            if label not in t_node.children:
                t_node.children[label] = MatchNode(label)
            t_node.children[label].values.update(s_child.values)
            dfs(t_node.children[label], s_child)
    dfs(target_tree.root, source_tree.root)
   
    return target_tree
        

def aggregate_digits_by_depth(tree):
    new_tree = NaryTree()
    
    def dfs(orig_node, new_node, depth):
        digit_children = {}
        regular_children = {}
        for label, child in orig_node.children.items():
            token = label.strip('.-')
            (digit_children if token.isdigit() else regular_children)[token] = child

        if digit_children:
            digit_values = list(map(int, digit_children.keys()))
            label_range = f"digits@{depth}:[{min(digit_values)},{max(digit_values)}]for:{len(digit_values)}"
            agg_node = new_node.children.setdefault(label_range, MatchNode(label_range))
            for child in digit_children.values():
                agg_node.values.update(child.values)
                dfs(child, agg_node, depth + 1)

        for label, child in regular_children.items():
            next_node = new_node.children.setdefault(label, MatchNode(label))
            next_node.values.update(child.values)
            dfs(child, next_node, depth + 1)

    dfs(tree.root, new_tree.root, 0)
    return new_tree

def load_and_match(plucked_trees, tree, etldp1, country_iso, conn, aggregated=False):
    c = conn.cursor()
    
    tokens = collect_tokens_by_level(tree.root)

    matches_list = [
        ("directional", geo.load_directional_terms(c), match_terms),
        ("GEO-classification", geo.load_geo_classification_terms(c), match_terms),
        ("UN-locode", set(x['locode'] for x in geo.load_un_locode(c, country_iso)), match_terms),
        ("UN-subdiv", set(x['code'] for x in geo.load_un_locode_subdiv(c, country_iso)), match_terms),
        ("GEO-names", geo.load_geo_names(c, country_iso), match_geonames)
    ]
    base_tree = tree
    for match_type, term_set, matcher in matches_list:
        match_result = matcher(tokens, term_set, match_type) if match_type != "GEO-names" else matcher(tokens, term_set)
        if match_result:
            #print(f"{match_type} matches: {match_result}")
            label = f"{match_type}:{country_iso}" if match_type not in MATCHERS[3:] else f"{match_type}"
            base_tree = build_modified_tree(base_tree, match_result, label, aggregated)
    
    if etldp1 in plucked_trees:
        plucked_trees[etldp1] = combine_trees(plucked_trees[etldp1], base_tree)
    else:
        plucked_trees[etldp1] = base_tree


def main():
    parser = argparse.ArgumentParser(description="Classify DNS patterns using Geo DB")
    parser.add_argument("input", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="Path to input pattern file")
    parser.add_argument("--geodb", default="geo_name_un_locode.db", help="Path to geo DB")
    parser.add_argument("--graph", default="normal", choices=["normal", "aggregated"], help="Graph aggregation option")
    parser.add_argument("-d", "--digits", action="store_true", help="Apply digits-aggregation")
    parser.add_argument("--export-json", type=str, help="Export all plucked trees as JSON files")
    parser.add_argument("--export-metrics", type=str, help="Path to save tree complexity metrics as CSV")
    args = parser.parse_args()

    df = pd.read_csv(args.input, sep='|', header=None, names=['patterntype', 'pattern', 'ip', 'etldp1', 'ipprefix', 'matchcount'])
    df['pattern_clean'] = df['pattern'].apply(normalize_namefill_pattern)
    df['country_iso'] = df['ip'].apply(get_iso_country)

    country_nan_count = 0
    trees, tree_complexity_metrics, plucked_trees, all_trees_dict = {}, {}, {}, {}
    for _, row in df.iterrows():
        pattern, etldp1, country_iso = row['pattern_clean'], row['etldp1'], row['country_iso']
        if pd.notna(pattern) and pd.notna(etldp1) and pd.notna(country_iso):
            try:
                key = f"{etldp1}_{country_iso}"
                trees.setdefault(key, NaryTree()).insert(pattern, etldp1)
            except ValueError:
                country_nan_count += 1
                print(f"{etldp1}resolved to ISO:{country_iso}")

    conn = geo.connect_geo_db(args.geodb)
    for key, tree in trees.items():
        etldp1, country = key.split('_')
        print(f"\nAnalyzing: {etldp1} (Country: {country})")
        load_and_match(plucked_trees, tree, etldp1, country, conn, aggregated=(args.graph == "aggregated"))
    
    # count the ambigous etldp1s
    count_ambigous = 0
    for etldp1, plucked_tree in plucked_trees.items():
        if args.digits:
            plucked_tree = aggregate_digits_by_depth(plucked_tree)
        tree_complexity_metrics[etldp1] = analyze_tree_complexity(plucked_tree)
        lines, _ = generate_mermaid_tree(plucked_tree.root, aggregated=(args.graph == "aggregated"))
        
        # store the trees/visualize and analyse
        all_trees_dict[f"{etldp1}_tree"] = NaryTree.tree_to_dict(plucked_tree.root)

        try:
            with open(f"mermaid_trees/{etldp1}_plucked_tree.mmd", 'w') as f:
                f.write("\n".join(lines))
        except FileNotFoundError:
            count_ambigous += 1
            with open(f"ambigous_etldp1/{count_ambigous}_plucked_tree.mmd", 'w') as f:
                f.write("\n".join(lines))

    metrics_df = plot_tree_metrics(tree_complexity_metrics)
    print(metrics_df.head())
    print(metrics_df.describe())
    print(f"total patterns: {sum(metrics_df.iloc[:,1])}")
    print(f"Couldn't process {country_nan_count} patterns!")
    if args.export_metrics:
        metrics_df.to_csv(args.export_metrics)
    if args.export_json:
        with gzip.open(args.export_json, 'wt', encoding='utf-8') as f:
            json.dump(all_trees_dict, f)
    conn.close()

if __name__ == "__main__":
    main()
