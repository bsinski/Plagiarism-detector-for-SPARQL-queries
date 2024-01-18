from zss.simple_tree import Node
from zss.compare import simple_distance
from queryParser import convert_query_text, unify_names


def convert_variable_name(variable):
    if variable.startswith("?"):
        return "?variable"
    return variable


def dict2tree(dictionary, node, convert_names = False):
    for key, value in dictionary.items():
        key = str(key)
        if isinstance(value, dict):
            child = dict2tree(value, Node(key))
            node.addkid(child)
        else:
            if isinstance(value, list):
                list_node = Node(key)
                for item in value:
                    if convert_names:
                        item = convert_variable_name(item)
                    if item is None:
                        item = "Noneee"
                    list_node.addkid(Node(str(item)))
                node.addkid(list_node)
            else:
                if convert_names:
                    value = convert_variable_name(value)
                if value is None:
                    value = "Noneee"
                if key is None:
                    key = "Noneee"
                value = str(value)
                node.addkid(Node(key).addkid(Node(value)))
    return node


def correct_node_equall_relations(node):
    children = node.children
    children_labels = [child.label for child in children] 
    if "op" in children_labels:
        # Getting the operation
        operation = children[children_labels.index("op")].children[0].label
        if operation == "=" or operation == "!=":
            for child in children:
                if child.label != "op":
                    child.label = "expr"
    elif "logic" in children_labels:
        operation = children[children_labels.index("logic")].children[0].label
        if operation == "and" or operation == "or":
            for child in children:
                if child.label != "logic":
                    child.label = "expr"
    return node

def correct_tree_relations(tree):
    for child in tree.children:
        child = correct_tree_relations(child)
    tree = correct_node_equall_relations(tree)
    return tree
    

def calculate_distance(query1, query2, verbose = False):
    node1 = Node("root")
    node2 = Node("root")
    query1['query'].pop('bgp')
    query2['query'].pop('bgp')
    tree1 = dict2tree(query1, node1)
    tree2 = dict2tree(query2, node2)
    tree1 = correct_tree_relations(tree1)
    tree2 = correct_tree_relations(tree2)
    if verbose:
        print(tree1.print_tree())
        print(tree2.print_tree())
    distance = simple_distance(tree1, tree2)
    print(f"Distance: {distance}")
    return distance, tree1, tree2


def compare_queries(text_query1, text_query2, verbose = False):
    query1 = convert_query_text(text_query1)
    query2 = convert_query_text(text_query2)
    query1, query2 = unify_names(query1, query2)
    distance, tree1, tree2 = calculate_distance(query1, query2, verbose=verbose)
    return distance
