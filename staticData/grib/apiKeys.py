
TMPFILE = 'gribkeys'
OUTFILE = 'apikeys.ttl'
#grib_keys_command = ['grib_keys', '-axT', 'GRIB2', '>', TMPFILE]


#make temp file

#subprocess.check_call(grib_keys_command)

outstr = '''#(C) British Crown Copyright 2011 - 2012, Met Office This file is part of metOcean-mapping.
#metOcean-mapping is free software: you can redistribute it and/or modify it under the terms of the
#GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License,
#or (at your option) any later version. metOcean-mapping is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#See the GNU Lesser General Public License for more details. You should have received a copy of the
#GNU Lesser General Public License along with metOcean-mapping. If not, see http://www.gnu.org/licenses/."

@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix gribapi: <http://def.ecmwf.int/api/grib/keys> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

'''

prefix = 'http://def.ecmwf.int/api/grib/keys/'

with open(TMPFILE) as keys:
    for line in keys:
        line = line.split('(')[0]
        if len(line)>0:
            line = line.strip()
            if not line.startswith('==='):
                outstr += '''<{pref}{line}> rdf:type skos:concept ;
                skos:prefLabel "{line}" ;
                .

                '''.format(pref=prefix,line=line)

with open(OUTFILE, 'w') as ttl:
    ttl.write(outstr)
    





