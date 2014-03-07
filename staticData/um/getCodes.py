import os
import subprocess
import urllib

base = 'http://reference.metoffice.gov.uk/system/query?'

fcqstr = '''prefix skos: <http://www.w3.org/2004/02/skos/core#>
construct {
 ?s skos:notation ?n .
  }
WHERE {
  select distinct ?s ?n
  WHERE{
   ?s ?p ?o .
  filter(regex(str(?s), "http://reference.metoffice.gov.uk/um/fieldcode/" ) )
  ?s skos:notation ?n .
  }
  }
'''

stqstr = '''prefix skos: <http://www.w3.org/2004/02/skos/core#>
construct {
 ?s skos:notation ?n .
  }
WHERE {
  select distinct ?s ?n
  WHERE{
   ?s ?p ?o .
  filter(regex(str(?s), "http://reference.metoffice.gov.uk/um/stash/" ) )
  ?s skos:notation ?n .
  }
  }
'''

fpath = os.path.dirname(__file__)

outputs = [(os.path.join(fpath, 'fieldcode.ttl'), fcqstr),
           (os.path.join(fpath, 'stashconcepts.ttl'), stqstr)]

for ofile, qstr in outputs:
    qstren = urllib.urlencode([('query', qstr),
                               ])

    url = base + qstren

    call = ['curl', '-H', 'Accept:text/turtle', url]

    print ' '.join(call)

    output = subprocess.check_output(call)

    with open(ofile, 'w') as newf:
        newf.write(output)

