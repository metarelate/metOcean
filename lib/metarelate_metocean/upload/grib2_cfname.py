import argparse
import copy
from collections import namedtuple
import requests
import sys
import warnings

import metarelate
import metarelate.fuseki as fuseki
from metarelate.prefixes import Prefixes

record = namedtuple('record', 'disc pcat pnum cfname units force')
expected = '|Disc|pCat|pNum|CFName|units|force_update(y/n)|'

def parse_file(fuseki_process, filehandle, userid, branchid):
    """
    file lines must be of the form
    |Disc|pCat|pNum|CFName|units|force_update(y/n)|
    with this as the header(the first line is skipped on this basis)


    """
    inputs = file_handle.read()
    lines = inputs.split('\n')
    if lines[0].strip() == expected:
        lines = lines[1:]
    else:
        raise ValueError('File headers not as expected')
    for line in lines:
        line = line.strip()
        lsplit = line.split('|')
        if len(lsplit) != 8:
            raise ValueError('unexpected line splitting; expected:\n'
                             '{}\ngot:\n{}'.format(expected, line))
        else:
            arecord = record(lsplit[1], lsplit[2], lsplit[3],
                             lsplit[4], lsplit[5], lsplit[6])
        make_grib2_mapping(fuseki_process, arecord, userid, branchid, force)

                
def cfname(name, units):
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
                                            metarelate.Item(units))
    acfnprop = metarelate.StatementProperty(metarelate.Item(pred, pred.split('/')[-1]),
                                            metarelate.Item(name, name.split('/')[-1]))
    cff = '{}Field'.format(pre['cfmodel'])
    acfcomp = metarelate.Component(None, cff, [acfnprop, acfuprop])
    return acfcomp

def make_grib2_mapping(fu_p, arecord, userid, branchid, force):
    pre = Prefixes()
    griburi = 'http://codes.wmo.int/grib2/codeflag/4.2/{d}-{c}-{i}'
    griburi = griburi.format(d=arecord.disc, c=arecord.pcat, i=arecord.pnum)
    req = requests.get(griburi)
    if req.status_code != 200:
        raise ValueError('unrecognised grib2 parameter code: {}'.format(griburi))
    gpd = 'http://codes.wmo.int/def/grib2/parameterId'
    agribprop = metarelate.StatementProperty(metarelate.Item(gpd),
                                            metarelate.Item(griburi))
    gribmsg = 'http://codes.wmo.int/def/codeform/GRIB-message'
    agribcomp = metarelate.Component(None, gribmsg, [agribprop])
    agribcomp.create_rdf(fu_p, graph=branchid)
    acfcomp = cfname(arecord.cfname, arecord.units)
    acfcomp.create_rdf(fu_p, graph=branchid)
    inv = '"True"'
    replaces = fu_p.find_valid_mapping(agribcomp, acfcomp, graph=branchid)
    if replaces:
        replaced = metarelate.Mapping(replaces.get('mapping'))
        replaced.populate_from_uri(fu_p, branchid)
        replaced.replaces = replaced.uri
        replaced.uri = None
        replaced.contributors = replaced.contributors + [userid]
        replaced.create_rdf(fu_p, graph=branchid)
    else:
        target_differs = fu_p.find_valid_mapping(agribcomp, None, graph=branchid)
        if target_differs:
            # msg = ('{} uses the same source with a different '
            #        'target\nSource:\n{}\nTarget:\n{}')
            # warnings.warn(msg.format(target_differs, agribcomp, acfcomp))
            #raise ValueError(msg.format(target_differs, agribcomp, acfcomp))
            replaced = metarelate.Mapping(target_differs.get('mapping'))
            replaced.populate_from_uri(fu_p, branchid)
            mr = _report(replaced)
            replaced.replaces = replaced.uri
            replaced.uri = None
            replaced.contributors = replaced.contributors + [userid]
            replaced.source = agribcomp
            replaced.target = acfcomp
            nr = _report(replaced)
            if not force:
                raise ValueError('You need to force replacing mapping \n'
                                 '{m} \nwith \n{n}\n'.format(m=mr, n=nr))
            replaced.create_rdf(fu_p, graph=branchid)
        else:
            amap = metarelate.Mapping(None, agribcomp, acfcomp,
                                      creator=userid, invertible=inv)
            amap.create_rdf(fu_p, graph=branchid)

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
        branchid = fuseki_process.branch_graph(args.user)
        with open(args.infile, 'r') as inputs:
            parse_file(fuseki_process, args.infile, args.user, branchid)
        fuseki_process.save(branchid)


if __name__ == '__main__':
    main()
