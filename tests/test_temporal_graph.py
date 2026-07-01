from mindriver.temporal_graph import TemporalGraph, edges_from_fact

def test_temporal_graph_probe_and_related():
    graph=TemporalGraph(); graph.add('MindRiver','supports','Neverend','sync notes',0.8)
    assert graph.probe('MindRiver')[0].target == 'Neverend'
    assert graph.related('MindRiver')['Neverend'] == 0.8

def test_edges_from_fact_extracts_entities():
    edges=edges_from_fact('MindRiver 支持 Neverend 的知识同步')
    assert edges
