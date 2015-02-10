import requests
from Queue import Queue
from collections import deque

from metarelate.thread import WorkerThread, MAXTHREADS


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
    qstr = ('SELECT ?amap ?long_name \n'
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
    resource_queue = Queue()
    resource_deque = deque()
    for result in results:
        std_url = stdn.format(result.get('long_name').strip('"').strip())
        resource_queue.put(TestUri(std_url, result.get('amap')))
        # run worker threads
    for i in range(MAXTHREADS):
        ExistsWorkerThread(resource_queue, resource_deque).start()
        # block progress until the queue is empty
    resource_queue.join()
    for resource in resource_deque:
        if resource.exists:
            ufails.append({'amap': resource.amap})
    val_errors_response = {'CF long name is a valid standard name':ufails}
    return val_errors_response

class TestUri(object):
    def __init__(self, uri, amap):
        self.uri = uri
        self.amap = amap
        self.exists = False

class ExistsWorkerThread(WorkerThread):
    def dowork(self, resource):
        response = requests.get(resource.uri)
        if response.status_code == 200:
            resource.exists = True

