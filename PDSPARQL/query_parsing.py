import rdflib
from rdflib.plugins import sparql
import re
import numpy as np 

def get_literal(literal):
    type = literal.datatype
    if type is not None:
        return {'value':literal.toPython(),"type":literal.datatype.toPython()}
    else:
        return {'value':literal.toPython(),"type":literal.datatype}
    

def get_variable(variable):
    return variable.toPython()


def parse_filterings(expression):
    if expression.name == 'RelationalExpression':
        if isinstance(expression['other'], rdflib.term.Literal):
            other = get_literal(expression['other'])
        else:
            other = get_variable(expression['other'])
        if isinstance(expression['expr'], rdflib.term.Literal):
            expr = get_literal(expression['expr'])
        else:
            expr = get_variable(expression['expr'])
        return {
            'op': expression['op'],
            'expr': expr,
            'other': other,
        }
    elif expression.name == 'ConditionalAndExpression':
        parsed_expression = {
            'logic' : 'and',
            'expr': parse_filterings(expression['expr']),
            'other': parse_filterings(expression['other'][0])
        }
        return parsed_expression
    elif expression.name == 'ConditionalOrExpression':
        parsed_expression = {
            'logic' : 'or',
            'expr': parse_filterings(expression['expr']),
            'other': parse_filterings(expression['other'][0])
        }
        return parsed_expression
    else:
        return None 
    
def parse_triple(triple):
    return {
        'subject': triple[0].toPython(),
        'predicate': triple[1].toPython(),
        'object': triple[2].toPython()
    }


def convert_to_query_structure(input_dict):
    query_dict = {
    }
    tmp_dict = input_dict['p']
    project = tmp_dict['PV']
    query_dict['project'] = [p.toPython() for p in project]
    
    try:
        order_condition = tmp_dict['p']['expr']
        query_dict['order'] = []
        for condition in order_condition:
            query_dict['order'].append(condition['expr'].toPython())
        tmp_dict = tmp_dict['p']
    except KeyError:
        pass
    
    try:
        filter_condition = tmp_dict['p']['expr']
        query_dict['filter'] = parse_filterings(filter_condition)
        tmp_dict = tmp_dict['p']
    except KeyError:
        pass
    
    try:
        bgp_triples = tmp_dict['p']['triples']
        query_dict['bgp'] = []
        for triple in bgp_triples:
            query_dict['bgp'].append(parse_triple(triple))
    except KeyError:
        pass

    return query_dict


def parse_prefixes(prefix_string):
    prefixes = {}
    pattern = re.compile(r'PREFIX\s+(\w+):\s*<(.+?)>')
    matches = pattern.findall(prefix_string)
    for match in matches:
        prefix, uri = match
        prefixes[prefix] = uri
    return prefixes


def convert_query_text(query_text):
    query_dict = {
        'prefixes': {},
        'query': {}
    }
    parse_results = sparql.parser.parseQuery(query_text)
    algebra_result = sparql.algebra.translateQuery(parse_results)
    algebra_dict = dict(algebra_result.algebra)
    query_dict['prefixes'] = parse_prefixes(query_text)
    query_dict['query'] = convert_to_query_structure(algebra_dict)
    return query_dict 
