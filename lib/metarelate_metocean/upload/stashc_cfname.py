import argparse
import copy
from collections import namedtuple
import requests
import sys


import metarelate
import metarelate.fuseki as fuseki
from metarelate.prefixes import Prefixes
from metarelate_metocean.upload.uploaders import cfname, update_mappingmeta

record = namedtuple('record', 'stash cfname units force')
expected = '|STASH(msi)|CFName|units|force_update(y/n)|'

def parse_file(fuseki_process, file_handle, userid, branchid):
    """
    file lines must be of the form
    |STASH(msi)|CFName|units|force_update(y/n)|
    with this as the header(the first line is skipped on this basis)

    this only runs a line if the complexity is set to 'n' or 'false'

    """
    inputs = file_handle.read()

    lines = inputs.split('\n')
    exp = expected
    new_mappings = []
    errors = []
    if lines[0].strip() == exp:
        lines = lines[1:]
    else:
        errors.append('line0: File headers not as expected:\n{}\n!=\n{}'
                      '\n'.format(expected, lines[0]))
    for n, line in enumerate(lines):
        i = n + 1
        line = line.strip()
        lsplit = line.split('|')
        if line and not line.startswith('#') and len(lsplit) != 6:
            errors.append('line{}: unexpected line splitting; expected:\n'
                          '{}\ngot:\n{}\n'.format(i, expected, line))
        elif line and not line.startswith('#'):
            arecord = record(lsplit[1].strip(), lsplit[2].strip(),
                             lsplit[3].strip(), lsplit[4].strip())
            if arecord.force not in ['y', 'n']:
                errors.append('line{}: force must be y or n, not {}'
                              '\n'.format(i, arecord.force))
            else:
                force = False
                if arecord.force == 'y':
                    force = True
            if arecord.cfname:
                amap, errs = make_stash_mapping(fuseki_process, 
                                                       arecord.stash, 
                                                       arecord.cfname,
                                                       arecord.units, 
                                                       userid, branchid, force)
                new_mappings.append(amap)
                if errs:
                    errors.append('line{}: {}'.format(i, '\n\t'.join(errs)))
            else:
                errors.append('line{}: no name provided'.format(i))
    if errors:
        raise ValueError('\n'.join(errors))
    # now all inputs are validated, create the triples in the tdb
    for amap in new_mappings:
        amap.source.create_rdf(fuseki_process, branchid)
        amap.target.create_rdf(fuseki_process, branchid)
        amap.create_rdf(fuseki_process, branchid)
                                    

def make_stash_mapping(fu_p, stashmsi, name, units, userid, branchid, force):
    errs = []
    pre = Prefixes()
    stashuri = '{p}{c}'.format(p=pre['moStCon'], c=stashmsi)
    req = requests.get(stashuri)
    if req.status_code != 200:
        errs.append('unrecognised stash code: {}'.format(stash))
    pred = metarelate.Item('{}stash'.format(pre['moumdpF3']),'stash')
    robj = metarelate.Item(stashuri, stashmsi)
    astashprop = metarelate.StatementProperty(pred, robj)
    ppff = '{}UMField'.format(pre['moumdpF3'])
    astashcomp = metarelate.Component(None, ppff, [astashprop])
    astashcomp.create_rdf(fu_p, graph=branchid)
    acfcomp = cfname(name, units)
    replaces = fu_p.find_valid_mapping(astashcomp, acfcomp, graph=branchid)
    if replaces:
        replaced = metarelate.Mapping(replaces.get('mapping'))
        replaced.populate_from_uri(fu_p, branchid)
        replaced = update_mappingmeta(replaced, userid)
        result = replaced
    else:
        target_differs = fu_p.find_valid_mapping(astashcomp, None, graph=branchid)
        if target_differs:
            replaced = metarelate.Mapping(target_differs.get('mapping'))
            replaced.populate_from_uri(fu_p, branchid)
            mr = _report(replaced)
            replaced = update_mappingmeta(replaced, userid)
            replaced.source = astashcomp
            replaced.target = acfcomp
            nr = _report(replaced)
            if not force:
                errs.append('You need to force replacing mapping \n'
                            '{m} \nwith \n{n}\nin order to process'
                            'this request'.format(m=mr, n=nr))
            result = replaced
        else:
            amap = metarelate.Mapping(None, astashcomp, acfcomp,
                                      creator=userid, invertible='"False"')
            result = amap
    return result, errs

def _report(mapping):
    mr = mapping.source.stash.notation
    mr += ' -> '
    try:
        mr += mapping.target.standard_name.notation
    except Exception:
        pass
    try:
        mr += mapping.target.long_name.notation
    except Exception:
        pass
    mr += '({})'.format(mapping.target.units.notation)
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
        fuseki_process.save(branchid)


if __name__ == '__main__':
    main()
