import requests

import metarelate
from metarelate.prefixes import Prefixes

def cfname(name, units):
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
    if units == '1':
        units = u'1'
    acfuprop = metarelate.StatementProperty(metarelate.Item(cfun,'units'),
                                            metarelate.Item(units, units))
    acfnprop = metarelate.StatementProperty(metarelate.Item(pred, pred.split('/')[-1]),
                                            metarelate.Item(name, name.split('/')[-1]))
    cff = '{}Field'.format(pre['cfmodel'])
    acfcomp = metarelate.Component(None, cff, [acfnprop, acfuprop])
    return acfcomp



def update_mappingmeta(replaced, userid):
    replaced.replaces = replaced.uri
    replaced.uri = None
    contribs = set(replaced.contributors)
    contribs.update([replaced.creator])
    replaced.contributors = list(contribs)
    replaced.creator = userid
    return replaced
