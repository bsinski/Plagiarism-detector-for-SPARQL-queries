import rdflib
from rdflib.plugins import sparql
import re
import numpy as np 
import copy

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
        if expression['op'] == '<':
            return{
                'op': '>',
                'expr': other,
                'other': expr
            }
        elif expression['op'] == '<=':
            return{
                'op': '>=',
                'expr': other,
                'other': expr
            }
        else:
            return {
                'op': expression['op'],
                'expr': expr,
                'other': other
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
    
def transform_aggregates(s):
    return s.replace('?__agg_', '?agg').replace('__', '')

def parse_triple(triple):
    return {
        'subject': triple[0].toPython(),
        'predicate': triple[1].toPython(),
        'object': triple[2].toPython()
    }

def parse_extends(expression):
    extends = []
    while expression.name == 'Extend':
        extends.append({'expr': transform_aggregates(expression['expr'].toPython()),'var':expression['var'].toPython()})
        expression = expression['p']
    return extends

def propagate_names(input_dict, variable_mapping):
    def replace_variable(var):
        return variable_mapping.get(var, var)

    def recursive_replace(obj):
        if isinstance(obj, list):
            return [recursive_replace(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: recursive_replace(value) for key, value in obj.items()}
        elif isinstance(obj, str) and obj.startswith('?'):
            return replace_variable(obj)
        else:
            return obj

    return recursive_replace(input_dict)

def parse_groupby(expression):
    
    parsed_expression = {
        'variables' :[],
        'aggregates': []
    } 
    aggregated_variables = []
    aggregations_dict = {}
    parsed_expression['variables'] = [variable.toPython() for variable in expression['p']['expr']]
    for agg in expression['A']:
        if agg.name == 'Aggregate_Sample' and 'distinct' in agg.keys():
            parsed_expression['aggregates'].append( {
                'type':'Sample',
                'variable': agg['vars'].toPython(),
                'res' : f"?aggr{len(aggregated_variables)}"
            })
            aggregations_dict[transform_aggregates(agg['res'].toPython())] = f"?aggr{len(aggregated_variables)}"
            aggregated_variables.append(transform_aggregates(agg['res'].toPython()))
        elif agg.name == 'Aggregate_Min':
            parsed_expression['aggregates'].append( {
                'type':'Min',
                'variable': agg['vars'].toPython(),
                'res' : f"?aggr{len(aggregated_variables)}"
            })
            aggregations_dict[transform_aggregates(agg['res'].toPython())] = f"?aggr{len(aggregated_variables)}"
            aggregated_variables.append(transform_aggregates(agg['res'].toPython()))
        elif agg.name == 'Aggregate_Max':
            parsed_expression['aggregates'].append( {
                'type':'Max',
                'variable': agg['vars'].toPython(),
                'res' : f"?aggr{len(aggregated_variables)}"
            })
            aggregations_dict[transform_aggregates(agg['res'].toPython())] = f"?aggr{len(aggregated_variables)}"
            aggregated_variables.append(transform_aggregates(agg['res'].toPython()))
        elif agg.name == 'Aggregate_Count':
            parsed_expression['aggregates'].append( {
                'type':'Count',
                'variable': agg['vars'].toPython(),
                'res' : f"?aggr{len(aggregated_variables)}"
            })
            aggregations_dict[transform_aggregates(agg['res'].toPython())] = f"?aggr{len(aggregated_variables)}"
            aggregated_variables.append(transform_aggregates(agg['res'].toPython()))
        elif agg.name == 'Aggregate_Sum':
            parsed_expression['aggregates'].append( {
                'type':'Sum',
                'variable': agg['vars'].toPython(),
                'res' : f"?aggr{len(aggregated_variables)}"
            })
            aggregations_dict[transform_aggregates(agg['res'].toPython())] = f"?aggr{len(aggregated_variables)}"
            aggregated_variables.append(transform_aggregates(agg['res'].toPython()))
        elif agg.name == 'Aggregate_Avg':
            parsed_expression['aggregates'].append( {
                'type':'Avg',
                'variable': agg['vars'].toPython(),
                'res' : f"?aggr{len(aggregated_variables)}"
            })
            aggregations_dict[transform_aggregates(agg['res'].toPython())] = f"?aggr{len(aggregated_variables)}"
            aggregated_variables.append(transform_aggregates(agg['res'].toPython()))
        elif agg.name == 'Aggregate_GroupConcat':
            parsed_expression['aggregates'].append( {
                'type':'GroupConcat',
                'variable': agg['vars'].toPython(),
                'res' : f"?aggr{len(aggregated_variables)}"
            })
            aggregations_dict[transform_aggregates(agg['res'].toPython())] = f"?aggr{len(aggregated_variables)}"
            aggregated_variables.append(transform_aggregates(agg['res'].toPython()))
    return parsed_expression,aggregated_variables,aggregations_dict
        
def convert_to_query_structure(input_dict):
    query_dict = {
    }
    tmp_dict = input_dict['p']
    project = tmp_dict['PV']
    query_dict['project'] = [p.toPython() for p in project]
    
    try:
        if tmp_dict['p'].name=='OrderBy':
            order_condition = tmp_dict['p']['expr']
            query_dict['order'] = []
            for condition in order_condition:
                query_dict['order'].append(condition['expr'].toPython())
            tmp_dict = tmp_dict['p']
    except KeyError:
        pass
    extends_dict = {}
    try:
        if tmp_dict['p'].name=='Extend':
            extends = parse_extends(tmp_dict['p'])
            for i in range(len(query_dict['project'])+1):
                tmp_dict = tmp_dict['p']
            grouped,aggregates,aggregates_dict = parse_groupby(tmp_dict)
            extends_agg =  [item for item in extends if item['expr'] in aggregates]
            
            for extend in extends_agg:
                extends_dict[extend['var']] = extend['expr']  
            query_dict['group'] = grouped
            tmp_dict = tmp_dict['p']
    except KeyError:
        pass
    
    try:
        if tmp_dict['p'].name=='Filter':
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
    if len(extends_dict) >0:
        result_dict = propagate_names(propagate_names(query_dict, extends_dict),aggregates_dict)
        return result_dict
    else:  
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

def rename_variables(triples1 ,triples2):
    dict1 = copy.deepcopy(triples1)
    dict2 = copy.deepcopy(triples2)
    subjects1 = {}
    predicates1 = {}
    objects1 = {}
    for triple in dict1:
        subject = triple['subject']
        if subject.startswith('?'):
            if subject in subjects1:
                triple['subject'] = subjects1[subject]
            else:
                subjects1[subject] = '?s' + str(len(subjects1))
                triple['subject'] = subjects1[subject]
        predicate = triple['predicate']
        if predicate.startswith('?'):
            if predicate in predicates1:
                triple['predicate'] = predicates1[predicate]
            else:
                predicates1[predicate] = '?p' + str(len(predicates1))
                triple['predicate'] = predicates1[predicate]
        object = triple['object']
        if object.startswith('?'):
            if object in objects1:
                triple['object'] = objects1[object]
            else:
                objects1[object] = '?o' + str(len(objects1))
                triple['object'] = objects1[object]
    transformed_triples = []
    already_in = False
    subjects2 = {}
    predicates2 = {}
    objects2 = {}
    for triple in dict2:
        mapped_value = False
        for triple_org in dict1:
            if triple_org['subject'] == triple['subject'] and not triple['subject'].startswith('?') and triple['object'].startswith('?') and triple['predicate'].startswith('?'):
                already_in = False
                for triple_transformed in transformed_triples:
                    if triple_org['subject'] == triple_transformed['subject'] and triple_org['object'] == triple_transformed['object'] and triple_org['predicate'] == triple_transformed['predicate']:
                        already_in = True
                        break
                if already_in:
                    continue
                objects2[triple['object']] = triple_org['object']
                triple['object'] = triple_org['object']
                predicates2[triple['predicate']] = triple_org['predicate']
                triple['predicate'] = triple_org['predicate']
                mapped_value = True
                break
            elif triple_org['predicate'] == triple['predicate'] and not triple['predicate'].startswith('?') and triple['object'].startswith('?') and triple['subject'].startswith('?'):
                already_in = False
                for triple_transformed in transformed_triples:
                    if triple_org['predicate'] == triple_transformed['predicate'] and triple_org['object'] == triple_transformed['object'] and triple_org['subject'] == triple_transformed['subject']:
                        already_in = True
                        break
                if already_in:
                    continue
                subjects2[triple['subject']] =triple_org['subject']
                triple['subject'] = triple_org['subject']
                objects2[triple['object']] = triple_org['object']
                triple['object'] = triple_org['object']
                mapped_value = True
                break
            elif triple_org['object'] == triple['object'] and not triple['object'].startswith('?') and triple['subject'].startswith('?') and triple['predicate'].startswith('?'):
                already_in = False
                for triple_transformed in transformed_triples:
                    if triple_org['object'] == triple_transformed['object'] and triple_org['subject'] == triple_transformed['subject'] and triple_org['predicate'] == triple_transformed['predicate']:
                        already_in = True
                        break
                if already_in:
                    continue
                subjects2[triple['subject']] = triple_org['subject']
                triple['subject'] = triple_org['subject']
                predicates2[triple['predicate']] = triple_org['predicate']
                triple['predicate'] = triple_org['predicate']
                mapped_value = True
                break
            elif triple_org['subject'] == triple['subject'] and not triple['subject'].startswith('?') and triple_org['predicate'] == triple['predicate'] and not triple['predicate'].startswith('?') and triple['object'].startswith('?'):
                already_in = False
                for triple_transformed in transformed_triples:
                    if triple_org['subject'] == triple_transformed['subject'] and triple_org['predicate'] == triple_transformed['predicate'] and triple_org['object'] == triple_transformed['object']:
                        already_in = True
                        break
                if already_in:
                    continue
                objects2[triple['object']] = triple_org['object']
                triple['object'] = triple_org['object']
                mapped_value = True
                break
            elif triple_org['subject'] == triple['subject'] and not triple['subject'].startswith('?') and triple_org['object'] == triple['object'] and not triple['object'].startswith('?') and triple['predicate'].startswith('?'):
                already_in = False
                for triple_transformed in transformed_triples:
                    if triple_org['subject'] == triple_transformed['subject'] and triple_org['object'] == triple_transformed['object'] and triple_org['predicate'] == triple_transformed['predicate']:
                        already_in = True
                        break
                if already_in:
                    continue
                predicates2[triple['predicate']] =triple_org['predicate']
                triple['predicate'] =triple_org['predicate']
                mapped_value = True
                break
            elif triple_org['predicate'] == triple['predicate'] and not triple['predicate'].startswith('?') and triple_org['object'] == triple['object'] and not triple['object'].startswith('?') and triple['subject'].startswith('?'):
                already_in = False
                for triple_transformed in transformed_triples:
                    if triple_org['subject'] == triple_transformed['subject'] and triple['object'] == triple_transformed['object'] and triple['predicate'] == triple_transformed['predicate']:
                        already_in = True
                        break
                if already_in:
                    continue
                subjects2[triple['subject']] = triple_org['subject']
                triple['subject'] = triple_org['subject']
                mapped_value = True
                break
            elif not triple_org['subject'].startswith('?') and not triple['subject'].startswith('?') and not triple_org['object'].startswith('?') and not triple['object'].startswith('?') and not triple_org['predicate'].startswith('?') and not triple['predicate'].startswith('?'):
                triple['predicate'] = predicates1[triple_org['predicate']]
                triple['object'] = objects1[triple_org['object']]
                triple['subject'] = subjects1[triple_org['subject']]
                mapped_value = True
                break
        if not mapped_value:
            if triple['subject'].startswith('?'):
                if triple['subject'] in subjects2:
                    triple['subject'] = subjects2[triple['subject']]
                else:
                    subjects2[triple['subject']] = '?s' + str(len(subjects2)+len(subjects1))
                    triple['subject'] = subjects2[triple['subject']]
            if triple['predicate'].startswith('?'):
                if triple['predicate'] in predicates2:
                    triple['predicate'] = predicates2[triple['predicate']]
                else:
                    predicates2[triple['predicate']] = '?p' + str(len(predicates2)+len(subjects1))
                    triple['predicate'] = predicates2[triple['predicate']]
            if triple['object'].startswith('?'):
                if triple['object'] in objects2:
                    triple['object'] = objects2[triple['object']]
                else:
                    objects2[triple['object']] = '?o' + str(len(objects2)+len(subjects1))
                    triple['object'] = objects2[triple['object']]
        transformed_triples.append(triple)
        mappings1 = {}
        mappings2 = {}
        mappings1.update(subjects1)
        mappings1.update(predicates1)
        mappings1.update(objects1)
        mappings2.update(subjects2)
        mappings2.update(predicates2)
        mappings2.update(objects2)
    return dict1,dict2,mappings1,mappings2

def unify_names(dict1, dict2):
    query_dict1 = copy.deepcopy(dict1)
    query_dict2 = copy.deepcopy(dict2)
    unified1, unified2, mappings1, mappings2 = rename_variables(query_dict1['query']['bgp'], query_dict2['query']['bgp'])
    query_dict1['query']['bgp'] = unified1
    query_dict2['query']['bgp'] = unified2
    query_dict1['query'] = propagate_names(query_dict1['query'], mappings1)
    query_dict2['query'] = propagate_names(query_dict2['query'], mappings2)
    return query_dict1, query_dict2