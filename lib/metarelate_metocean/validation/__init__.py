import requests


def _comp_fails(fuseki_process, comp_fails):
    """
    find all valid mappings which use acomp as a source or target
    """
    val_errors = []
    for failure in comp_fails:
        qstr = ('SELECT ?amap \n'
                'WHERE {\n'
                'GRAPH <http://metarelate.net/mappings.ttl> {\n'
                '{?amap mr:source %(c)s .}\n'
                'UNION\n'
                '{?amap mr:target %(c)s .}\n'
                'MINUS {?amap ^dc:replaces+ ?anothermap}\n'
                '}}' % {'c':failure.get('acomp')})
        results = fuseki_process.run_query(qstr)
        val_errors = val_errors + results
    return val_errors

    

def cfunits(fuseki_process):
    """
    Validate that cf units rdfobject literals are 
    able to be parsed by udunits
    """
    qstr = ('SELECT ?acomp ?units \n'
            'WHERE {\n'
            'GRAPH <http://metarelate.net/concepts.ttl> {\n'
            '?acomp <http://def.scitools.org.uk/cfdatamodel/units> ?units'
            '}}\n')
    results = fuseki_process.run_query(qstr)
    ufails = []
    # for result in results:
    #     try:
    #         Unit(result.get('units').strip('"'))
    #     except ValueError:
    #         ufails.append(result)
    val_errors = _comp_fails(fuseki_process, ufails)
    val_errors_response = {'CF units not parseable':val_errors}
    return val_errors_response

# def longnamespace(fuseki_process):
#     """
#     """
#     qstr = ('SELECT ?acomp ?long_name \n'
#             'WHERE {\n'
#             'GRAPH <http://metarelate.net/concepts.ttl> {\n'
#             '?acomp <http://def.scitools.org.uk/cfdatamodel/long_name> ?long_name'
#             '}}\n')
#     results = fuseki_process.run_query(qstr)
#     ufails = []
#     for result in results:
#         if len(result.get('long_name').split(' ')) > 1:
#             ufails.append(result)
#     val_errors = _comp_fails(fuseki_process, ufails)
#     val_errors_response = {'Spaces in CF long_name':val_errors}
#     return val_errors_response    

def cflongnameisstd(fuseki_process):
    """
    """
    stdn = 'http://vocab.nerc.ac.uk/standard_name/{}/'
    val_errors = []
    qstr = ('SELECT ?acomp ?long_name \n'
            'WHERE {\n'
            'GRAPH <http://metarelate.net/concepts.ttl> {\n'
            '?acomp <http://def.scitools.org.uk/cfdatamodel/long_name> ?long_name'
            '}}\n')
    results = fuseki_process.run_query(qstr)
    ufails = []
    for result in results:
        std_url = stdn.format(result.get('long_name').strip('"'))
        resp = requests.get(std_url)
        if resp.status_code == 200:
            ufails.append(result)
    val_errors = _comp_fails(fuseki_process, ufails)
    val_errors_response = {'CF long name is a valid standard name':val_errors}
    return val_errors_response
