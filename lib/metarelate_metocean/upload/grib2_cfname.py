import argparse
import copy
from collections import namedtuple
import requests
import sys
import warnings

import metarelate
import metarelate.fuseki as fuseki
from metarelate_metocean.upload.uploaders import (cfname, update_mappingmeta,
                                                  grib2_comp)

record = namedtuple('record', 'disc pcat pnum cfname units force')
expected = '|Disc|pCat|pNum|CFName|units|force_update(y/n)|'

def parse_file(fuseki_process, file_handle, userid, branchid):
    """
    file lines must be of the form
    |Disc|pCat|pNum|CFName|units|force_update(y/n)|
    with this as the header(the first line is skipped on this basis)


    """
    inputs = file_handle.read()
    lines = inputs.split('\n')
    new_mappings = []
    errors = []
    if lines[0].strip() == expected:
        lines = lines[1:]
    else:
        errors.append('line0: File headers not as expected:\n{}\n!=\n{}'
                      '\n'.format(expected, lines[0]))
    new_mappings = []
    for n, line in enumerate(lines):
        i = n + 1
        line = line.strip()
        lsplit = line.split('|')
        if len(lsplit) != 8:
            if line:
                errors.append('line{}: unexpected line splitting; expected:\n'
                              '{}\ngot:\n{}'.format(i, expected, line))
        else:
            arecord = record(lsplit[1], lsplit[2], lsplit[3],
                             lsplit[4], lsplit[5], lsplit[6])
            if arecord.force not in ['y', 'n']:
                errors.append('line{}: force must be y or n, not {}'
                              '\n'.format(i, arecord.force))
            else:
                force = False
                if arecord.force == 'y':
                    force = True
            amap, errs = make_grib2_mapping(fuseki_process, arecord, userid, branchid, force)
            new_mappings.append(amap)
            if errs:
                errors.append('line{}: {}'.format(i, '\n\t'.join(errs)))
    if errors:
        raise ValueError('||\n'.join(errors))
    # now all inputs are validated, create the triples in the tdb
    for amap in new_mappings:
        amap.source.create_rdf(fuseki_process, branchid)
        amap.target.create_rdf(fuseki_process, branchid)
        amap.create_rdf(fuseki_process, branchid)


def make_grib2_mapping(fu_p, arecord, userid, branchid, force):
    errs = []
    agribcomp, errs = grib2_comp(arecord, errs)
    acfcomp = cfname(arecord.cfname, arecord.units)
    inv = '"True"'
    replaces = fu_p.find_valid_mapping(agribcomp, acfcomp, graph=branchid)
    if replaces:
        replaced = metarelate.Mapping(replaces.get('mapping'))
        replaced.populate_from_uri(fu_p, branchid)
        replaced = update_mappingmeta(replaced, userid)
        result = replaced
    else:
        target_differs = fu_p.find_valid_mapping(agribcomp, None, graph=branchid)
        if target_differs:
            replaced = metarelate.Mapping(target_differs.get('mapping'))
            replaced.populate_from_uri(fu_p, branchid)
            replaced = update_mappingmeta(replaced, userid)
            mr = _report(replaced)
            replaced.source = agribcomp
            replaced.target = acfcomp
            nr = _report(replaced)
            if not force:
                errs.append('forcing replacement of '
                            '{m} with {n}'.format(m=mr, n=nr))
            result = replaced
        else:
            amap = metarelate.Mapping(None, agribcomp, acfcomp,
                                      creator=userid, invertible=inv)
            result = amap
    return result, errs

def _report(mapping):
    mr = mapping.source.grib2_parameter.rdfobject.data
    mr += ' ->'
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
        #fuseki_process.load()
        branchid = fuseki_process.branch_graph(args.user)
        with open(args.infile, 'r') as inputs:
            parse_file(fuseki_process, inputs, args.user, branchid)
        fuseki_process.save(branchid)


if __name__ == '__main__':
    main()
