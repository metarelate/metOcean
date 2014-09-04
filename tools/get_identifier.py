import time

import metarelate.fuseki as fu
import requests



def getAReallySimpleQ():
    return ('SELECT ?key ?value'
            ' WHERE {'
            ' {SERVICE %(ps)s '
            '{SELECT ?key ?value WHERE {'
            '  %(p)s skos:notation ?key .'
            '}}}'
            '{SERVICE %(os)s '
            '{SELECT ?value WHERE {'
            '  %(o)s skos:notation ?value'
            '}}}'
            '}')


def getAMoreComplexQ():
    return ('SELECT ?key ?value'
            ' WHERE {'
            '  {SELECT ?key ?value'
            '   WHERE {'
            '    {SERVICE %(ps)s '
            '     {SELECT ?key ?value WHERE {'
            '      %(p)s skos:notation ?key .'
            '    }}}'
            '    {SERVICE %(os)s '
            '     {SELECT ?value WHERE {'
            '      %(o)s skos:notation ?value'
            '    }}}'
            '       }}'
            ' UNION '
            '  {SELECT ?key ?value'
            '   WHERE {'
            '    {SERVICE %(os)s '
            '     {SELECT ?key ?value ?idr ?rdfobj ?rdfobjnot WHERE {'
            '      %(o)s <http://metarelate.net/vocabulary/index.html#identifier> ?idr ;'
            '       ?idr ?rdfobj .'
            '      OPTIONAL {?idr skos:notation ?key . }'
            '      OPTIONAL {?rdfobj skos:notation ?rdfobjnot}'
            '      BIND((IF(isURI(?rdfobj), ?rdfobjnot, ?rdfobj)) AS ?value)'
            '     }}'
            '    }'
            '  }}'
            '}')

def getq():
    return ('SELECT ?key ?value'
            ' WHERE {'
            '  {SELECT ?key ?value'
            '   WHERE {'
            '    {SERVICE %(ps)s '
            '     {SELECT ?key ?value WHERE {'
            '      %(p)s skos:notation ?key .'
            '    }}}'
            '    {SERVICE %(os)s '
            '     {SELECT ?value WHERE {'
            '      %(o)s skos:notation ?value'
            '    }}}'
            '       }}'
            ' UNION '
            '  {SELECT ?key ?value'
            '   WHERE {'
            '    {SERVICE %(ps)s '
            '     {SELECT ?key ?value WHERE {'
            '      %(p)s skos:notation ?key .'
            '      FILTER(isLiteral(%(o)s))'
            '      BIND(%(o)s as ?value)'
            '    }}}'
            '       }}'
            ' UNION '
            '  {SELECT ?key ?value'
            '   WHERE {'
            '    {SERVICE %(os)s '
            '     {SELECT ?key ?value ?idr ?rdfobj ?rdfobjnot WHERE {'
            '      %(o)s <http://metarelate.net/vocabulary/index.html#identifier> ?idr ;'
            '       ?idr ?rdfobj .'
            '      OPTIONAL {?idr skos:notation ?key . }'
            '      OPTIONAL {?rdfobj skos:notation ?rdfobjnot}'
            '      {SERVICE %(ps)s'
            '       {SELECT ?idr ?key ?rdfobj ?rdfobjnot WHERE {'
            '        OPTIONAL {?idr skos:notation ?key . }'
            '        OPTIONAL {?rdfobj skos:notation ?rdfobjnot}'
            '       }}}'
            '      BIND((IF(isURI(?rdfobj), ?rdfobjnot, ?rdfobj)) AS ?value)'
            '     }}'
            '    }'
            '  }}'
            '}')

def testunit(fuseki_process, qstr):
    predicate = '<http://def.scitools.org.uk/cfdatamodel/units>'
    pspq = '<http://def.scitools.org.uk/system/query?>'
    rdfobject = '"W m-2"'
    rospq = '<http://def.scitools.org.uk/system/query?>'

    aqstr = qstr % {'p':predicate, 'o':rdfobject, 'ps':pspq, 'os':rospq}

    result = fuseki_process.run_query(aqstr)
    expected = [{u'value': '"W m-2"', u'key': '"units"'}]
    result.sort()
    if result != expected:
        raise ValueError('unexpected result:\n{}'.format(result))
    # print(str(len(result)) + ':\n' + str(result))
    
def teststdname(fuseki_process, qstr):
    predicate = '<http://def.scitools.org.uk/cfdatamodel/standard_name>'
    pspq = '<http://def.scitools.org.uk/system/query?>'
    rdfobject = '<http://vocab.nerc.ac.uk/standard_name/surface_snow_melt_heat_flux>'
    #rdfobject = '<http://vocab.nerc.ac.uk/collection/P07/current/CFSN0255/>'
    #rospq = '<http://vocab.nerc.ac.uk/query???>'
    rospq = '<http://def.scitools.org.uk/system/query?>'

    aqstr = qstr % {'p':predicate, 'o':rdfobject, 'ps':pspq, 'os':rospq}

    result = fuseki_process.run_query(aqstr)
    expected = []
    result.sort()
    # if result != expected:
    #     raise ValueError('unexpected result:\n{}'.format(result))
    print(str(len(result)) + ':\n' + str(result))
    

def testg1p(fuseki_process, qstr):

    predicate = '<http://codes.wmo.int/def/grib1/parameter>'
    pspq = '<http://codes.wmo.int/system/query?>'
    rdfobject = '<http://reference.metoffice.gov.uk/grib/grib1/ecmwf--98/128-129>'
    rospq = '<http://reference.metoffice.gov.uk/system/query?>'

    aqstr = qstr % {'p':predicate, 'o':rdfobject, 'ps':pspq, 'os':rospq}

    result = fuseki_process.run_query(aqstr)
    expected = [{u'key': '"centre"', u'value': u'98'}, 
                {u'key': '"editionNumber"', u'value': u'1'}, 
                {u'key': '"indicatorOfParameter"', u'value': u'129'}, 
                {u'key': '"table2version"', u'value': u'128'}]
    result.sort()
    if result != expected:
        raise ValueError('unexpected result:\n{}'.format(result))
    #print(str(len(result)) + ':\n' + str(result))

def testg2p(fuseki_process, qstr):

    predicate = '<http://codes.wmo.int/def/grib2/parameter>'
    pspq = '<http://codes.wmo.int/system/query?>'
    rdfobject = '<http://codes.wmo.int/grib2/codeflag/4.2/0-1-27>'
    rospq = '<http://codes.wmo.int/system/query?>'

    aqstr = qstr % {'p':predicate, 'o':rdfobject, 'ps':pspq, 'os':rospq}

    result = fuseki_process.run_query(aqstr)
    expected = [{u'value': u'0', u'key': '"discipline"'}, 
                {u'value': u'2', u'key': '"editionNumber"'}, 
                {u'value': u'1', u'key': '"parameterCategory"'}, 
                {u'value': u'27', u'key': '"parameterNumber"'}]
    result.sort()
    if result != expected:
        raise ValueError('unexpected result:\n{}'.format(result))
    #print(str(len(result)) + ':\n' + str(result))


def teststash(fuseki_process, qstr):
    predicate = '<http://reference.metoffice.gov.uk/um/c4/stash/Stash>'
    pspq = '<http://reference.metoffice.gov.uk/system/query?>'
    rdfobject = '<http://reference.metoffice.gov.uk/um/stash/m01s02i208> '
    rospq = '<http://reference.metoffice.gov.uk/system/query?>'

    aqstr = qstr % {'p':predicate, 'o':rdfobject, 'ps':pspq, 'os':rospq}
    result = fuseki_process.run_query(aqstr)
    #print result
    result, = result
    if not result == {u'value': '"m01s02i208"', u'key': '"stash"'}:
        raise ValueError('unexpected result:\n{}'.format(result))
    

def main(fuseki_process):
    teststash(fuseki_process, getq())
    testg2p(fuseki_process, getq())
    testg1p(fuseki_process, getq())
    testunit(fuseki_process, getq())
    teststdname(fuseki_process, getq())

if __name__ == '__main__':
    with fu.FusekiServer() as fu_p:
        main(fu_p)
