import argparse
import copy
from collections import namedtuple
import requests
import sys


import metarelate
import metarelate.fuseki as fuseki
from metarelate.prefixes import Prefixes

def parse_file(fuseki_process, file_handle, userid, branchid):
    """
    file lines must be of the form
    STASH(msi)|CFName|units|further_complexity
    with this as the header(the first line is skipped on this basis)

    this only runs a line if the complexity is set to 'n' or 'false'

    """
    record = namedtuple('record', 'stash cfname units force')
    expected = '|STASH(msi)|CFName|units|force_update(y/n)|'
    inputs = file_handle.read()

    lines = inputs.split('\n')
    exp = expected
    if lines[0].strip() == exp:
        lines = lines[1:]
    else:
        raise ValueError('File headers not as expected')
    for line in lines:
        line = line.strip()
        lsplit = line.split('|')
        if line and not line.startswith('#') and len(lsplit) != 6:
            raise ValueError('unexpected line splitting; expected:\n'
                             '{}\ngot:\n{}'.format(expected, line))
        elif line and not line.startswith('#'):
            arecord = record(lsplit[1].strip(), lsplit[2].strip(),
                             lsplit[3].strip(), lsplit[4].strip())
            if arecord.force not in ['y', 'n']:
                raise ValueError('force must be y or n, not {}'.format(arecord.force))
            else:
                force = False
                if arecord.force == 'y':
                    force = True
            if arecord.cfname:
                make_stash_mapping(fuseki_process, arecord.stash, arecord.cfname,
                                   arecord.units, userid, branchid, force)
            else:
                raise ValueError('no name provided')


                
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

def make_stash_mapping(fu_p, stashmsi, name, units, userid, branchid, force):
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
    astashcomp.create_rdf(fu_p, graph=branchid)
    acfcomp = cfname(fu_p, name, units)
    acfcomp.create_rdf(fu_p, graph=branchid)
    replaces = fu_p.find_valid_mapping(astashcomp, acfcomp, graph=branchid)
    if replaces:
        replaced = metarelate.Mapping(replaces.get('mapping'))
        replaced.populate_from_uri(fu_p)
        replaced.replaces = replaced.uri
        replaced.uri = None
        replaced.contributors = replaced.contributors + [userid]
        replaced.create_rdf(fu_p, graph=branchid)
    else:
        target_differs = fu_p.find_valid_mapping(astashcomp, None, graph=branchid)
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
            if not force:
                raise ValueError('You need to force replacing mapping \n'
                                 '{m} \nwith \n{n}\n'.format(m=mr, n=nr))
            replaced.create_rdf(fu_p, graph=branchid)
        else:
            amap = metarelate.Mapping(None, astashcomp, acfcomp,
                                      creator=userid, invertible='"False"')
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
        # make a branch
        branchid = fuseki_process.branch_graph(args.user)
        with open(args.infile, 'r') as inputs:
            parse_file(fuseki_process, inputs, args.user, branchid)
        import pdb; pdb.set_trace()
        fuseki_process.save(branchid)


if __name__ == '__main__':
    main()
