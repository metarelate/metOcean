import argparse
import copy
from collections import namedtuple
import json
import requests
import sys


from metarelate import (Item, ComponentProperty, StatementProperty,
                        Mapping, Component)
import metarelate.fuseki as fuseki

mrpref = '<http://www.metarelate.net/metOcean'

def parse_file(fuseki_process, file_handle, userid, branchid):
    inputs = file_handle.read()
    lines = inputs.split('\n')
    if len(lines) != 1 and not(len(lines) == 2 and not lines[1]):
        raise ValueError('file must be exactly one line long')
    line = lines[0]
    amapping = json.loads(line)
    mapping = make_mapping(amapping, fuseki_process, branchid)
    mapping.source.create_rdf(fuseki_process, branchid)
    mapping.target.create_rdf(fuseki_process, branchid)
    mapping.create_rdf(fuseki_process, branchid)

    
def make_mapping(amapping, fuseki_process, branchid):
    source_dict = amapping.pop('mr:source')
    amapping['mr:source'] = make_component(source_dict, fuseki_process, branchid)
    target_dict = amapping.pop('mr:target')
    amapping['mr:target'] = make_component(target_dict, fuseki_process, branchid)
    id = amapping.pop('@id', None)
    mapping = Mapping(None, source=amapping.get('mr:source'),
                      target=amapping.get('mr:target'),
                      invertible=amapping.get('mr:invertible', None),
                      creator=amapping.get('dc:creator', None),
                      note=amapping.get('dc:note', None),
                      replaces=amapping.get('dc:replaces', None),
                      valuemaps=amapping.get('mr:hasValueMap', None),
                      rightsHolders=amapping.get('dc:rightsHolder', None), 
                      rights=amapping.get('dc:rights', None),
                      contributors=amapping.get('dc:contributors', None),
                      dateAccepted=amapping.get('dc:dateAccepted', None))
    return mapping

    
def make_component(comp_dict, fuseki_process, branchid):
    id = comp_dict.pop('@id', None)
    com_type, = comp_dict.pop('rdf:type', None)
    props = []
    for key, vals in comp_dict.iteritems():
        for val in vals:
            prop_id = ''
            if isinstance(val, dict):
                prop_id = val.pop('@id', '')
            if key == 'rdf:type':
                pass
            elif prop_id and prop_id.startswith(mrpref):
                pcomp = make_component(val, fuseki_process, branchid)
                pcomp.create_rdf(fuseki_process, branchid)
                props.append(ComponentProperty(Item(key), pcomp))
            else:
                props.append(StatementProperty(Item(key), Item(val)))
    component = Component(None, com_type=com_type, properties=props)
    
    return component


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
        fuseki_process.load()
        branchid = fuseki_process.branch_graph(args.user)
        with open(args.infile, 'r') as inputs:
            parse_file(fuseki_process, inputs, args.user, branchid)
        fuseki_process.save(branchid)


if __name__ == '__main__':
    main()
