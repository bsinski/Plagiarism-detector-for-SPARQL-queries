from zss.simple_tree import Node
from zss.compare import simple_distance
from queryParser import convert_query_text, unify_names


def convert_variable_name(variable):
    '''
    Convert a variable name to a standardized format.

    Args:
        variable (str): The variable name to be converted.

    Returns:
        str: The converted variable name.

    '''
    if variable.startswith("?"):
        return "?variable"
    return variable


def dict2tree(dictionary, node, convert_names = False):
    """
    Converts a dictionary into a tree structure represented by nodes.

    Args:
        dictionary (dict): The dictionary to be converted into a tree.
        node (Node): The root node of the tree.
        convert_names (bool, optional): Flag indicating whether to convert variable names. Defaults to False.

    Returns:
        Node: The root node of the converted tree.
    """
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
                    value = "None"
                if key is None:
                    key = "None"
                value = str(value)
                node.addkid(Node(key).addkid(Node(value)))
    return node


def correct_node_equall_relations(node):
    """
    Corrects the labels of the children nodes in the given node to "expr" if the operation is "=" or "!=".
    If the operation is "and" or "or", it also corrects the labels of the children nodes to "expr".
    
    Args:
        node (Node): The root to a tree be corrected.
    
    Returns:
        Node: The root of the corrected node.
    """
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
    """
    Calculates the distance between two queries.

    Args:
        query1 (dict): The first query.
        query2 (dict): The second query.
        verbose (bool, optional): Whether to print additional information. Defaults to False.

    Returns:
        tuple: A tuple containing the distance between the queries, and the corresponding query trees.
    """
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
    """
    Compares two SPARQL queries and calculates the distance between them.

    Parameters:
    text_query1 (str): The first SPARQL query to compare.
    text_query2 (str): The second SPARQL query to compare.
    verbose (bool, optional): If True, additional information will be printed during the comparison. Defaults to False.

    Returns:
    float: The distance between the two queries.
    """
    query1 = convert_query_text(text_query1)
    query2 = convert_query_text(text_query2)
    query1, query2 = unify_names(query1, query2)
    distance, tree1, tree2 = calculate_distance(query1, query2, verbose=verbose)
    return distance
