import requests

subformat_predicates = ['<http://codes.wmo.int/def/common/edition>']

def cfunits(fuseki_process, graph=None):
    """
    Validate that cf units rdfobject literals are 
    able to be parsed by udunits
    """
    graphs = ('FROM NAMED <http://metarelate.net/concepts.ttl>\n'
              'FROM NAMED <http://metarelate.net/mappings.ttl>\n')
    if graph:
        graphs += 'FROM NAMED <http://metarelate.net/{}concepts.ttl>\n'.format(graph)
        graphs += 'FROM NAMED <http://metarelate.net/{}mappings.ttl>\n'.format(graph)
    stdn = 'http://vocab.nerc.ac.uk/standard_name/{}/'
    val_errors = []
    qstr = ('SELECT ?amap \n'
            '%s'
            'WHERE {\n'
            'GRAPH ?g {\n'
            '{?amap rdf:type mr:Mapping ;'
            'mr:source ?acomp .}'
            'UNION'
            '{?amap rdf:type mr:Mapping ;'
            'mr:target ?acomp .}'
            'MINUS {?amap ^dc:replaces+ ?anothermap}\n'
            '}\n'
            'GRAPH <http://metarelate.net/concepts.ttl> {\n'
            '?acomp <http://def.scitools.org.uk/cfdatamodel/units> ?units'
            '}}\n' % graphs)
    results = fuseki_process.run_query(qstr)
    ufails = []
    # for result in results:
    #     try:
    #         Unit(result.get('units').strip('"'))
    #     except ValueError:
    #         ufails.append(result)
    val_errors_response = {'CF units not parseable':val_errors}
    return val_errors_response

def cflongnameisstd(fuseki_process, graph=None):
    # needs threading: slow
    """
    """
    graphs = ('FROM NAMED <http://metarelate.net/concepts.ttl>\n'
              'FROM NAMED <http://metarelate.net/mappings.ttl>\n')
    if graph:
        graphs += 'FROM NAMED <http://metarelate.net/{}concepts.ttl>\n'.format(graph)
        graphs += 'FROM NAMED <http://metarelate.net/{}mappings.ttl>\n'.format(graph)
    stdn = 'http://vocab.nerc.ac.uk/standard_name/{}/'
    val_errors = []
    qstr = ('SELECT ?amap \n'
            '%s'
            'WHERE {\n'
            'GRAPH ?gm {\n'
            '{?amap rdf:type mr:Mapping ;'
            'mr:source ?acomp .}'
            'UNION'
            '{?amap rdf:type mr:Mapping ;'
            'mr:target ?acomp .}'
            'MINUS {?amap ^dc:replaces+ ?anothermap}\n'
            '}\n'
            'GRAPH ?gc {\n'
            '?acomp <http://def.scitools.org.uk/cfdatamodel/long_name> ?long_name'
            '}}\n' % graphs)
    results = fuseki_process.run_query(qstr)
    ufails = []
    for result in results:
        std_url = stdn.format(result.get('long_name').strip('"').strip())
        resp = requests.get(std_url)
        if resp.status_code == 200:
            ufails.append(result)
    val_errors = ufails
    val_errors_response = {'CF long name is a valid standard name':val_errors}
    return val_errors_response

