import argparse
import copy
from collections import namedtuple
import requests
import sys
import warnings

import metarelate
import metarelate.fuseki as fuseki
from metarelate.prefixes import Prefixes

record = namedtuple('record', 'disc pcat pnum cfname units')

def parse_file(fuseki_process, afile, userid):
    """
    file lines must be of the form
    STASH(msi)|CFName|units|further_complexity
    with this as the header(the first line is skipped on this basis)

    this only runs a line if the complexity is set to 'n' or 'false'

    """
    expected = 'Disc|pCat|pNum|CFName|units'
    with open(afile, 'r') as inputs:
        lines = inputs.readlines()
        if lines[0].strip() == expected:
            lines = lines[1:]
        else:
            raise ValueError('File headers not as expected')
        for line in lines:
            line = line.strip()
            lsplit = line.split('|')
            if len(lsplit) != 5:
                raise ValueError('unexpected line splitting; expected:\n'
                                 '{}\ngot:\n{}'.format(expected, line))
            else:
                arecord = record(lsplit[0], lsplit[1], lsplit[2], lsplit[3],
                                 lsplit[4])
            make_stash_mapping(fuseki_process, arecord, userid)

                
def cfname(fu_p, name, units):
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

def make_grib2_mapping(fu_p, arecord, userid):
    pre = Prefixes()
    griburi = 'http://codes.wmo.int/grib2/codeflag/4.2/{d}-{c}-{i}'
    griburi = griburi.format(d=arecord.disc, c=arecord.pcat, i=arecord.pnum)
    req = requests.get(griburi)
    if req.status_code != 200:
        raise ValueError('unrecognised stash code: {}'.format(griburi))
    gpd = 'http://codes.wmo.int/def/grib2/parameterId'
    agribprop = metarelate.StatementProperty(metarelate.Item(gpd),
                                            metarelate.Item(griburi))
    gribmsg = 'http://codes.wmo.int/def/codeform/GRIB-message'
    agribcomp = metarelate.Component(None, gribmsg, [agribprop])
    agribcomp.create_rdf(fu_p)
    acfcomp = cfname(fu_p, arecord.cfname, arecord.units)
    acfcomp.create_rdf(fu_p)
    inv = '"True"'
    replaces = fu_p.find_valid_mapping(agribcomp, acfcomp)
    if replaces:
        replaced = metarelate.Mapping(replaces.get('mapping'))
        replaced.populate_from_uri(fu_p)
        replaced.replaces = replaced.uri
        replaced.uri = None
        replaced.contributors = replaced.contributors + [userid]
        replaced.create_rdf(fu_p)
    else:
        target_differs = fu_p.find_valid_mapping(agribcomp, None)
        if target_differs:
            msg = ('{} uses the same source with a different '
                   'target\nSource:\n{}\nTarget:\n{}')
            warnings.warn(msg.format(target_differs, agribcomp, acfcomp))
            #raise ValueError(msg.format(target_differs, agribcomp, acfcomp))
            replaced = metarelate.Mapping(target_differs.get('mapping'))
            replaced.populate_from_uri(fu_p)
            replaced.replaces = replaced.uri
            replaced.uri = None
            replaced.contributors = replaced.contributors + [userid]
            replaced.source = agribcomp
            replaced.target = acfcomp
            replaced.create_rdf(fu_p)
        else:
            amap = metarelate.Mapping(None, agribcomp, acfcomp,
                                      creator=userid, invertible=inv)
            amap.create_rdf(fu_p)

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
