import requests

import metarelate
from metarelate.prefixes import Prefixes

pre = Prefixes()

def cfname(name, units):
    """Create a new Component for the CF name and units."""

    # Fail if unit not udunits parseable
    # checkunit = Unit(units)
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

def stash_comp(stashmsi, errs):
    """Create a new Component from the provided stash code. """
    stashuri = '{p}{c}'.format(p=pre['moStCon'], c=stashmsi)
    headers = {'content-type': 'application/ld+json', 'Accept': 'application/ld+json'}
    req = requests.get(stashuri, headers=headers)
    if req.status_code != 200:
        errs.append('unrecognised stash code: {}'.format(stashuri))
    pred = metarelate.Item('{}stash'.format(pre['moumdpF3']),'stash')
    robj = metarelate.Item(stashuri, stashmsi)
    astashprop = metarelate.StatementProperty(pred, robj)
    ppff = '{}UMField'.format(pre['moumdpF3'])
    astashcomp = metarelate.Component(None, ppff, [astashprop])
    return (astashcomp, errs)

def grib2_comp(arecord, errs):
    """Create a new Component from the provided GRIB2 parameter. """
    griburi = 'http://codes.wmo.int/grib2/codeflag/4.2/{d}-{c}-{i}'
    griburi = griburi.format(d=arecord.disc, c=arecord.pcat, i=arecord.pnum)
    req = requests.get(griburi)
    if req.status_code != 200:
        errs.append('unrecognised grib2 parameter code: {}'.format(griburi))
    gpd = 'http://codes.wmo.int/def/grib2/parameterId'
    agribprop = metarelate.StatementProperty(metarelate.Item(gpd, 
                                                             'grib2_parameter'),
                                            metarelate.Item(griburi))
    gribmsg = 'http://codes.wmo.int/def/codeform/GRIB-message'
    agribcomp = metarelate.Component(None, gribmsg, [agribprop])
    return (agribcomp, errs)

def update_mappingmeta(replaced, userid):
    replaced.replaces = replaced.uri
    replaced.uri = None
    contribs = set(replaced.contributors)
    contribs.update([replaced.creator])
    replaced.contributors = list(contribs)
    replaced.creator = userid
    return replaced
