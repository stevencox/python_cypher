import itertools
import networkx as nx

tokens = (
    'LBRACKET',
    'RBRACKET',
    'LPAREN',
    'RPAREN',
    'COLON',
    'RIGHT_ARROW',
    'MATCH',
    'RETURN',
    'NAME',
    'WHITESPACE',
    'LCURLEY',
    'RCURLEY',
    'COMMA',
    'QUOTE',
    'INTEGER',
    'STRING',
    'KEY',)


t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COLON = r':'
t_WHITESPACE = r'[ ]+'
t_RIGHT_ARROW = r'-->'
t_QUOTE = r'"'
t_LCURLEY = r'{'
t_RCURLEY = r'}'
t_COMMA = r','
t_STRING = r'"[A-Za-z0-9]+"'


t_ignore = r' '


def t_error(t):
    print 'error'


def t_MATCH(t):
    r'MATCH'
    return t


def t_RETURN(t):
    r'RETURN'
    return t


def t_NAME(t):
    r'[A-Z]+[a-z0-9]*'
    return t


def t_KEY(t):
    r'[A-Za-z]+[0-9]*'
    return t


def t_INTEGER(t):
    r'[0-9]+'
    return int(t)

import ply.lex as lex
lexer = lex.lex()

import ply.yacc as yacc

atomic_facts = []
next_anonymous_variable = 0

start = 'match_return'

class AtomicFact(object):
    """ maybe useful, maybe not. """
    pass


class ClassIs(AtomicFact):
    def __init__(self, designation, class_name):
        self.designation = designation
        self.class_name = class_name


class EdgeExists(AtomicFact):
    def __init__(self, node_1, node_2, direction=None, edge_label=None):
        self.node_1 = node_1
        self.node_2 = node_2
        self.direction = direction


class AttributeHasValue(AtomicFact):
    def __init__(self, designation, attribute, value):
        self.designation = designation
        self.attribute = attribute
        self.value = value


class Node(object):
    '''A node specification -- a set of conditions and a designation.'''
    def __init__(self, node_class=None, designation=None,
                 attribute_conditions=None):
        self.node_class = node_class
        self.designation = designation
        self.attribute_conditions = attribute_conditions or {}


class AttributeConditionList(object):
    '''A bunch of AttributeHasValue objects in a list'''
    def __init__(self, attribute_list=None):
        global atomic_facts
        self.attribute_list = attribute_list or {}


def p_node_clause(p):
    '''node_clause : LPAREN NAME COLON RPAREN
                   | LPAREN NAME COLON KEY RPAREN
                   | LPAREN NAME COLON KEY condition_list RPAREN'''
    global next_anonymous_variable
    global atomic_facts
    if len(p) == 5:
        # Just a class name
        p[0] = Node(node_class=p[2],
                    designation='_v' + str(next_anonymous_variable),
                    attribute_conditions={})
        next_anonymous_variable += 1
    elif len(p) == 6:
        # Node class name and variable
        p[0] = Node(node_class=p[2], designation=p[4], attribute_conditions={})
    elif len(p) == 7:
        p[0] = Node(node_class=p[2], designation=p[4],
                    attribute_conditions=p[5])
    # Record the atomic facts
    atomic_facts.append(ClassIs(p[0].designation, p[0].node_class)) 
    for attribute, value in p[0].attribute_conditions.iteritems():
        atomic_facts.append(AttributeHasValue(p[0].designation, attribute, value))


class Relationship(object):
    def __init__(self, node_1, node_2, relationship_type=None,
                 min_depth=None, max_depth=None, arrow_direction=None):
        self.left_node = node_1
        self.right_node = node_2
        self.relationship_type = relationship_type
        self.min_depth = min_depth
        self.arrow_direction = arrow_direction


def p_relationship(p):
    '''relationship : node_clause RIGHT_ARROW node_clause'''
    global atomic_facts
    if p[2] == t_RIGHT_ARROW:
        p[0] = Relationship(p[1], p[3], arrow_direction='left_right')
        EdgeExists(p[0].designation, p[2].designation, direction='left_right')
    else:
        print 'unhandled case?'


class VariableList(object):
    '''A list of variables, as in RETURN statements, e.g.'''
    def __init__(self, obj1, obj2):
        part1 = [obj1] if isinstance(obj1, str) else obj1.variables
        part2 = [obj2] if isinstance(obj2, str) else obj2.variables
        self.variables = part1 + part2


def p_condition(p):
    '''condition_list : KEY COLON STRING
                      | condition_list COMMA condition_list
                      | LCURLEY condition_list RCURLEY'''
    global atomic_facts
    if len(p) == 4 and p[2] == ':':
        p[0] = {p[1]: p[3].replace('"', '')}
    elif len(p) == 4 and p[2] == ',':
        p[0] = p[1]
        p[1].update(p[3])
    elif len(p) == 4 and isinstance(p[2], dict):
        p[0] = p[2]


class Literals(object):
    def __init__(self, literal_list=None):
        self.literal_list = literal_list


def p_literals(p):
    '''literals : node_clause
                | literals COMMA literals
                | literals RIGHT_ARROW literals'''
    if len(p) == 2:
        p[0] = Literals(literal_list=[p[1]])
    elif len(p) == 4 and p[2] == t_COMMA:
        p[0] = Literals(p[1].literal_list + p[3].literal_list)
    elif len(p) == 4 and p[2] == t_RIGHT_ARROW:
        p[0] = p[1]
        p[0].literal_list += p[3].literal_list
        print p[1].literal_list[-1], '-->', p[3].literal_list[0]
    else:
        print 'unhandled case in literals...'


class MatchReturnQuery(object):
    def __init__(self, literals=None, return_variables=None):
        self.literals = literals
        self.return_variables = return_variables


def p_match_return(p):
    '''match_return : MATCH literals return_variables'''
    print 'in match_return'
    p[0] = MatchReturnQuery(literals=p[2], return_variables=p[3])


def p_error(p):
    import pdb; pdb.set_trace()
    print 'error.'


class ReturnVariables(object):
    def __init__(self, variable):
        self.variable_list = [variable]


def p_return_variables(p):
    '''return_variables : RETURN KEY
                        | return_variables COMMA KEY'''
    if len(p) == 3:
        p[0] = ReturnVariables(p[2])
    elif len(p) == 4:
        p[1].variable_list.append(p[3])
        p[0] = p[1]


sample = 'MATCH (SOMECLASS:x {bar : "baz", foo:"goo"})-->(ANOTHERCLASS:), (LASTCLASS:y) RETURN x, y'
# sample = '(IMACLASS:x {bar:"baz"})'
# sample = '(IMACLASS:x)'
lexer.input(sample)
tok = lexer.token()
while tok:
    print tok
    tok = lexer.token()

parser = yacc.yacc()
result = parser.parse(sample)


# Now we make a little graph for testing
g = nx.Graph()
g.add_node('node_1', {'class': 'SOMECLASS', 'foo': 'goo', 'bar': 'baz'})
g.add_node('node_2', {'class': 'ANOTHERCLASS', 'foo': 'not_bar'})
g.add_node('node_3', {'class': 'LASTCLASS', 'foo': 'goo', 'bar': 'notbaz'})
g.add_node('node_4', {'class': 'SOMECLASS', 'foo': 'not goo', 'bar': 'baz'})

g.add_edge('node_1', 'node_2')
g.add_edge('node_2', 'node_3')
g.add_edge('node_4', 'node_2')

# Let's enumerate the possible assignments
all_designations = set()
for fact in atomic_facts:
    if hasattr(fact, 'designation') and fact.designation is not None:
        all_designations.add(fact.designation)
all_designations = sorted(list(all_designations))

domain = g.nodes()
for domain_assignment in itertools.product(*[domain] * len(all_designations)):
    var_to_element = {all_designations[index]: element for index, element
                      in enumerate(domain_assignment)}
    element_to_var = {v: k for k, v in var_to_element.iteritems()}
    sentinal = True
    for atomic_fact in atomic_facts:
        if isinstance(atomic_fact, ClassIs):
            var_class = g.node[var_to_element[atomic_fact.designation]].get('class', None)
            var = atomic_fact.designation
            desired_class = atomic_fact.class_name
            if var_class != desired_class:
                sentinal = False
        if isinstance(atomic_fact, AttributeHasValue):
            attribute = atomic_fact.attribute
            desired_value = atomic_fact.value
            value = g.node[var_to_element[atomic_fact.designation]].get(attribute, None)
            if value != desired_value:
                sentinal = False
    if sentinal:
        print var_to_element
