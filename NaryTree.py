import re 

class MatchNode:
    def __init__(self, label: str):
        self.label = label
        self.children: dict[str, MatchNode] = {}
        self.values: set[str] = set()

class NaryTree:
    def __init__(self, root="."):
        self.root = MatchNode(root)

    def insert(self, fqdn: str, etldp1=None):
        tokens = NaryTree.generate_tokens(fqdn, etldp1)
        node = self.root
        for token in tokens:
            if token not in node.children:
                node.children[token] = MatchNode(token)
                
            node = node.children[token]

    def __str__(self):
        lines = []

        def recurse(node, depth=0):
            label_info = f"{node.label}"
            if node.values:
                label_info += f" [values: {len(node.values)}]"
            lines.append("  " * depth + label_info)
            for child in node.children.values():
                recurse(child, depth + 1)

        recurse(self.root)
        return "\n".join(lines)
    
    @staticmethod   
    def tree_to_dict(node):
        result = {}

        result['label'] = node.label
        if node.values:
            result['values'] = list(node.values)

        if node.children:
            result['children'] = {
                label: NaryTree.tree_to_dict(child)
                for label, child in node.children.items()
            }

        return result


    @staticmethod    
    def generate_tokens(fqdn: str, etldp1: str = None):
        """
        Generate tokens where the first child of the root is the etldplus1 (e.g., 'comcast.net'),
        and the rest of the FQDN is tokenized in reverse, keeping '.' and '-' markers.
        """
        fqdn = fqdn.strip().lower()
        
        if not fqdn or not etldp1 or not fqdn.endswith(etldp1):
            raise ValueError("invalid FQDN or etldplus1")

        # Remove etldplus1 to get the rest of the FQDN
        stripped_fqdn = fqdn[:-len(etldp1)].rstrip('.')
        
        # Token list begins with the etldplus1
        tokens = [f'.{etldp1}']

        if stripped_fqdn:
            parts = stripped_fqdn.split('.')[::-1]
            for part in parts:
                if '-' in part:
                    sub_parts = re.split(r'(?<=\w)-', part)
                    for i, sub in enumerate(sub_parts):
                        tokens.append(f'.{sub}' if i == 0 else f'-{sub}')
                else:
                    tokens.append(f'.{part}')
        
        return tokens

