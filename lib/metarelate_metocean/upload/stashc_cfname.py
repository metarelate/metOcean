import argparse
import copy
from collections import namedtuple
import requests
import sys
import warnings

import metarelate
import metarelate.fuseki as fuseki
from metarelate.prefixes import Prefixes

def parse_file(fuseki_process, afile, userid):
    """
    file lines must be of the form
    STASH(msi)|CFName|units|further_complexity
    with this as the header(the first line is skipped on this basis)

    this only runs a line if the complexity is set to 'n' or 'false'

    """
    record = namedtuple('record', 'stash cfname units complex')
    expected = '|STASH(msi)|CFName|units|further_complexity|'
    with open(afile, 'r') as inputs:
        lines = inputs.readlines()
        exp = expected
        if lines[0].strip() == exp:
            lines = lines[1:]
        else:
            raise ValueError('File headers not as expected')
        for line in lines:
            line = line.strip()
            lsplit = line.split('|')
            if len(lsplit) != 6:
                raise ValueError('unexpected line splitting; expected:\n'
                                 '{}\ngot:\n{}'.format(expected, line))
            else:
                arecord = record(lsplit[1].strip(), lsplit[2].strip(),
                                 lsplit[3].strip(), lsplit[4].strip())
            if arecord.cfname and arecord.complex == 'n' or arecord.complex.lower() == 'false':
                make_stash_mapping(fuseki_process, arecord.stash, arecord.cfname,
                                   arecord.units, userid)
            else:
               print('skipping unprocess complex line\n{}'.format(line))

                
def cfname(fu_p, name, units):
    # fail if unit not udunits parseable
    # checkunit = Unit(units)
    pre = Prefixes()
    standard_name = '{p}{c}'.format(p=pre['cfnames'], c=name)
    req = requests.get(standard_name)
    if req.status_code == 200:
        name = standard_name
        pred = '{}standard_name'.format(pre['cfmodel'])
    else:
        pred = '{}long_name'.format(pre['cfmodel'])
    cfun = '{}units'.format(pre['cfmodel'])
    acfuprop = metarelate.StatementProperty(metarelate.Item(cfun,'units'),
                                            metarelate.Item(units, units))
    acfnprop = metarelate.StatementProperty(metarelate.Item(pred, pred.split('/')[-1]),
                                            metarelate.Item(name, name.split('/')[-1]))
    cff = '{}Field'.format(pre['cfmodel'])
    acfcomp = metarelate.Component(None, cff, [acfnprop, acfuprop])
    return acfcomp

def make_stash_mapping(fu_p, stashmsi, name, units, userid):
    pre = Prefixes()
    stashuri = '{p}{c}'.format(p=pre['moStCon'], c=stashmsi)
    req = requests.get(stashuri)
    if req.status_code != 200:
        raise ValueError('unrecognised stash code: {}'.format(stash))
    pred = metarelate.Item('{}stash'.format(pre['moumdpF3']),'stash')
    robj = metarelate.Item(stashuri, stashmsi)
    astashprop = metarelate.StatementProperty(pred, robj)
    ppff = '{}UMField'.format(pre['moumdpF3'])
    astashcomp = metarelate.Component(None, ppff, [astashprop])
    astashcomp.create_rdf(fu_p)
    acfcomp = cfname(fu_p, name, units)
    acfcomp.create_rdf(fu_p)
    replaces = fu_p.find_valid_mapping(astashcomp, acfcomp)
    if replaces:
        replaced = metarelate.Mapping(replaces.get('mapping'))
        replaced.populate_from_uri(fu_p)
        replaced.replaces = replaced.uri
        replaced.uri = None
        replaced.contributors = replaced.contributors + [userid]
        replaced.create_rdf(fu_p)
    else:
        target_differs = fu_p.find_valid_mapping(astashcomp, None)
        if target_differs:
            replaced = metarelate.Mapping(target_differs.get('mapping'))
            replaced.populate_from_uri(fu_p)
            mr = _report(replaced) 
            replaced.replaces = replaced.uri
            replaced.uri = None
            replaced.contributors = replaced.contributors + [userid]
            replaced.source = astashcomp
            replaced.target = acfcomp
            nr = _report(replaced)
            warnings.warn('Replacing Mapping \n{m} \nwith \n{n}\n'.format(m=mr, n=nr))
            replaced.create_rdf(fu_p)
        else:
            amap = metarelate.Mapping(None, astashcomp, acfcomp,
                                      creator=userid, invertible='"False"')
            amap.create_rdf(fu_p)

def _report(mapping):
    mr = mapping.source.stash.notation
    mr += '\n'
    try:
        mr += mapping.target.standard_name.notation
    except Exception:
        pass
    try:
        mr += mapping.target.long_name.notation
    except Exception:
        pass
    mr += '\n'
    mr += mapping.target.units.notation
    return mr
    


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', type=str, help='file path for input file')
    parser.add_argument('user', help='uri of the metOcean user')
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    with fuseki.FusekiServer() as fuseki_process:
        fuseki_process.load()
        parse_file(fuseki_process, args.infile, args.user)
        fuseki_process.save()


if __name__ == '__main__':
    main()
