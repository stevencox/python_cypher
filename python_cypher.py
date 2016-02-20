import itertools
import networkx as nx
from cypher_tokenizer import *
from cypher_parser import *


class CypherParserBaseClass(object):
    def __init__(self):
        self.tokenizer = cypher_tokenizer
        self.parser = cypher_parser

    def parse(self, input):
        return self.parser.parse(input)

    def matching_nodes(self, graph_object, query_string):
        result = self.parse(query_string)
        all_designations = set()
        for fact in atomic_facts:
            if hasattr(fact, 'designation') and fact.designation is not None:
                all_designations.add(fact.designation)
        all_designations = sorted(list(all_designations))

        domain = self._get_domain(g)
        for domain_assignment in itertools.product(*[domain] * len(all_designations)):
            var_to_element = {all_designations[index]: element for index, element
                              in enumerate(domain_assignment)}
            element_to_var = {v: k for k, v in var_to_element.iteritems()}
            sentinal = True
            for atomic_fact in atomic_facts:
                if isinstance(atomic_fact, ClassIs):
                    var_class = self._node_class(g.node[
                        var_to_element[atomic_fact.designation]])
                    var = atomic_fact.designation
                    desired_class = atomic_fact.class_name
                    if var_class != desired_class:
                        sentinal = False
                        break
                if isinstance(atomic_fact, AttributeHasValue):
                    attribute = atomic_fact.attribute
                    desired_value = atomic_fact.value
                    value = self._node_attribute_value(g.node[
                        var_to_element[atomic_fact.designation]], attribute)
                    if value != desired_value:
                        sentinal = False
                        break
                if isinstance(atomic_fact, EdgeExists):
                    import pdb; pdb.set_trace()
            if sentinal:
                yield var_to_element


class CypherToNetworkx(CypherParserBaseClass):
    def _get_domain(self, obj):
        return obj.nodes()

    def _node_attribute_value(self, node, attribute):
        return node.get(attribute, 'None')

    def _edge_exists(self, source, target, edge_class=None, directed=True):
        sentinal = True
        if source not in g.edge or target not in g.edge[source]:
            sentinal = False
        return sentinal

    def _node_class(self, node, class_key='class'):
        return node.get(class_key, None)


if __name__ == '__main__':
    sample = ','.join(['MATCH (x:SOMECLASS {bar : "baz"',
                       'foo:"goo"})-->(:ANOTHERCLASS)',
                       '(y:LASTCLASS) RETURN x, y'])

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
    my_parser = CypherToNetworkx()
    for matching_assignment in my_parser.matching_nodes(g, sample):
        print matching_assignment
