import json
import re
from anytree import Node, RenderTree, PreOrderIter
from anytree.exporter import DotExporter
from anytree.search import find, findall


# TODO make the color scheme dynamic
COLOR_SCHEME = ["aliceblue", "antiquewhite", "azure", "coral", "palegreen"]


class TaxonomyFormatException(Exception):
    pass


class TaxonomyParser:

    """
    This class is a wrapper on a Tree class from the anytree library to hold
    different taxonomies read from a JSON representation

    Attributes
    ----------
    prefix: str with the prefix character for each level in the JSON representation
    nodes: dict with node name str as key and anytree Node instance as value which contains all the nodes of the taxonomy tree
    root_key: str identifying the root node for fast retrieval
    """

    def __init__(self, level_prefix = "L"):
        self.prefix = level_prefix
        self.nodes = {}
        self.root_key = None

    def find_by_name(self, name) -> Node:
        """
        Retrieve a node by its name

        Parameters
        ----------
        name: str holding the name to be looked for

        Returns
        -------
        node: an anytree Node instance with the seeked node
        """
        root = self.nodes[self.root_key]
        node = find(root, lambda node: node.name == name)
        return node

    def find_by_keyword(self, keyword) -> Node:
        """
        Find the node whose regex matches the event type ID given as input

        Parameters
        ----------
        ev_type: str holding the event type ID to look for

        Returns
        -------
        node: an anytree Node instance with the seeked node
        """
        def match_regex(node):
            has_regex = hasattr(node, "regex") and node.regex is not None
            if has_regex:
                matched = [re.search(r, keyword) for r in node.regex]
                if any(matched):
                    return node

        root = self.nodes[self.root_key]
        nodes = findall(root, filter_=match_regex)
        return nodes

    def get_leaves(self):
        """
        Get all the leaf nodes in the tree
        This function is used for fast retrieval of the regex to be applied to event types

        Returns
        -------
        a List of anytree Node instances holding the leaves data
        """
        res = []
        root = self.nodes[self.root_key]        
        for node in PreOrderIter(root):
            if len(node.children) == 0:
                res.append(node)
        return res

    def export(self, full=False):
        """
        Export tree into graphviz format in both *.dot file and image *.png file

        Parameters
        ----------
        full: boolean value, if True also the regex mappings are printed in the resulting file
        """
        def nodeattr_fn(node):
            return f'style=filled color={COLOR_SCHEME[node.depth]}'

        def nodename_fn(node):
            nl = "\n"
            name = node.name
            if hasattr(node, "regex"):
                name = f"""
{node.name}
-----------
{nl.join(node.regex)}
"""
            return name

        root = self.nodes[self.root_key]
        dot = DotExporter(
            root,
            nodenamefunc=nodename_fn if full else None,
            nodeattrfunc=nodeattr_fn,
            options=[
                'graph [layout = dot, ranksep="1.5", nodesep="0.7"]',
                'rankdir ="LR"',
                'node [fontname="Arial"]'
            ]
        )
        dot.to_dotfile(f"./{self.root_key}.dot")
        dot.to_picture(f"./{self.root_key}.png")

    def __str__(self):
        """
        ASCII representation of the tree similarly to a directory structure

        Returns
        -------
        msg: a str containing the output taxonomy visualization
        """
        msg = """"""
        root = self.nodes[self.root_key]
        for pre, _, node in RenderTree(root):
            msg += f"{pre}{node.name}\n"
        return msg

    def read_from_json(self, fname):
        """
        Read the taxonomy from a JSON file given as input
        The JSON file needs to have the following format:

        {
            "L0": [
                {
                    "name": "level0",
                }
            ],
            "L1": [
                {
                    "name": "level1",
                    "parent": "level0",
                    "regex": "(.*)"
                }
            ]
        }

        Parameters
        ----------
        fname: str with the name of the file containing the taxonomy
        """

        self.nodes = {}
        try:
            with open(fname, "r") as f:
                data = json.load(f)
                n_levels = len(list(data.keys()))

                # read the root node
                root = data[f"{self.prefix}0"][0]
                name = root["name"]
                _ = root.pop("name")
                
                self.nodes[name] = Node(name, **root)
                self.root_key = name

                # populate the tree
                for k in range(1, n_levels):
                    
                    key = f"{self.prefix}{k}"
                    nodes = data[key]

                    for n in nodes:
                        try:
                            assert "name" in n
                            name = n["name"]
                            _ = n.pop("name")
                            parent = n["parent"]
                            _ = n.pop("parent")
                            
                            self.nodes[name] = Node(
                                name,
                                parent=self.nodes[parent],
                                **n
                            )
                        except AssertionError:
                            print(f"Malformed node representation: {n}")
                        except KeyError:
                            print(f"Detected a dangling node: {n['name']}")

                return taxonomy
