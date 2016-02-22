import argparse
import copy
from collections import namedtuple
import requests
import sys
import warnings

import metarelate
import metarelate.fuseki as fuseki
from metarelate.prefixes import Prefixes
from metarelate_metocean.upload.uploaders import (cfname, update_mappingmeta,
                                                  stash_comp, grib2_comp)
import metarelate_metocean.upload.stashc_cfname as stcf
import metarelate_metocean.upload.grib2_cfname as g2cf

record = namedtuple('record', 'stash cfname units disc pcat pnum force')
expected = '|STASH(msi)|CFName|units|Disc|pCat|pNum|force_update(y/n)|'

def parse_file(fuseki_process, file_handle, userid, branchid):
    """
    file lines must be of the form
    |STASH(msi)|CFName|units|Disc|pCat|pNum|force_update(y/n)|
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
        if len(lsplit) != 9:
            if line:
                errors.append('line{}: unexpected line splitting; expected:\n'
                              '{}\ngot:\n{}'.format(i, expected, line))
        else:
            arecord = record(lsplit[1].strip(), lsplit[2].strip(),
                             lsplit[3].strip(), lsplit[4].strip(),
                             lsplit[5].strip(), lsplit[6].strip(),
                             lsplit[7].strip())
            if arecord.force not in ['y', 'n']:
                errors.append('line{}: force must be y or n, not {}'
                              '\n'.format(i, arecord.force))
            else:
                force = False
                if arecord.force == 'y':
                    force = True
            smap, serrs, gmap, gerrs = make_mappings(fuseki_process, arecord, userid,
                                       branchid, arecord.force)
            new_mappings.append(smap)
            new_mappings.append(gmap)
            if serrs:
                errors.append('line{}: {}'.format(i, '\n\t'.join(serrs)))
            if gerrs:
                errors.append('line{}: {}'.format(i, '\n\t'.join(gerrs)))
    if errors:
        raise ValueError('||\n'.join(errors))
    # now all inputs are validated, create the triples in the tdb
    for amap in new_mappings:
        amap.source.create_rdf(fuseki_process, branchid)
        amap.target.create_rdf(fuseki_process, branchid)
        amap.create_rdf(fuseki_process, branchid)

def make_mappings(fu_p, arecord, userid, branchid, force):
    serrs = []
    gerrs = []
    astashcomp, serrs = stash_comp(arecord.stash, serrs)
    agribcomp, gerrs = grib2_comp(arecord, gerrs)
    acfcomp = cfname(arecord.cfname, arecord.units)

    replaces = fu_p.find_valid_mapping(astashcomp, acfcomp, graph=branchid)
    if replaces:
        replaced = metarelate.Mapping(replaces.get('mapping'))
        replaced.populate_from_uri(fu_p, branchid)
        replaced = update_mappingmeta(replaced, userid)
        smap = replaced
    else:
        target_differs = fu_p.find_valid_mapping(astashcomp, None, graph=branchid)
        if target_differs:
            replaced = metarelate.Mapping(target_differs.get('mapping'))
            replaced.populate_from_uri(fu_p, branchid)
            mr = stcf._report(replaced)
            replaced = update_mappingmeta(replaced, userid)
            replaced.source = astashcomp
            replaced.target = acfcomp
            nr = stcf._report(replaced)
            if not force:
                serrs.append('forcing replacement of '
                            '{m} with {n}'.format(m=mr, n=nr))
            smap = replaced
        else:
            smap = metarelate.Mapping(None, astashcomp, acfcomp,
                                      creator=userid, invertible='"False"')

    inv = '"True"'
    replaces = fu_p.find_valid_mapping(agribcomp, acfcomp, graph=branchid)
    if replaces:
        replaced = metarelate.Mapping(replaces.get('mapping'))
        replaced.populate_from_uri(fu_p, branchid)
        replaced = update_mappingmeta(replaced, userid)
        gmap = replaced
    else:
        target_differs = fu_p.find_valid_mapping(agribcomp, None, graph=branchid)
        if target_differs:
            replaced = metarelate.Mapping(target_differs.get('mapping'))
            replaced.populate_from_uri(fu_p, branchid)
            replaced = update_mappingmeta(replaced, userid)
            mr = g2cf._report(replaced)
            replaced.source = agribcomp
            replaced.target = acfcomp
            nr = g2cf._report(replaced)
            if not force:
                gerrs.append('forcing replacement of '
                            '{m} with {n}'.format(m=mr, n=nr))
            gmap = replaced
        else:
            gmap = metarelate.Mapping(None, agribcomp, acfcomp,
                                      creator=userid, invertible=inv)

    return (smap, serrs, gmap, gerrs)

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
