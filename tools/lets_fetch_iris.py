import metarelate
from metarelate.prefixes import Prefixes
from metarelate.fuseki import FusekiServer

from iris.fileformats import um_cf_map
from iris.fileformats.grib import _grib_cf_map as grib_cf_map

ppff = 'http://reference.metoffice.gov.uk/um/f3/UMField'
Stash = 'http://reference.metoffice.gov.uk/um/c4/stash/Stash'

cff = 'http://def.scitools.org.uk/cfmodel/Field'
cfsn = 'http://def.scitools.org.uk/cfmodel/standard_name'
cfln = 'http://def.scitools.org.uk/cfmodel/long_name'
cfun = 'http://def.scitools.org.uk/cfmodel/units'

marqh = '<http://www.metarelate.net/metOcean/people/marqh>'

pre = Prefixes()


def _cfname(fu_p, cfname):
    standard_name = None
    long_name = None
    if cfname.standard_name:
        standard_name = '{p}{c}'.format(p=pre['cfnames'],
                                        c=cfname.standard_name)
        if cfname.long_name:
            raise ValueError('standard name and long name defined for'
                             ' {}'.format(stash))
    elif cfname.long_name:
        long_name = cfname.long_name
    if cfname.units is not None:
        units = cfname.units
    else:
        raise ValueError('no units')
    name = False
    if standard_name is not None:
        name = standard_name
        pred = cfsn
    elif long_name is not None:
        name = long_name
        pred = cfln
    acfuprop = metarelate.StatementProperty(metarelate.Item(cfun, 'units'),
                                            metarelate.Item(units))
    if name:
        acfnprop = metarelate.StatementProperty(metarelate.Item(pred, pred.split('/')[-1]),
                                                metarelate.Item(name, name.split('/')[-1]))
        acfcomp = metarelate.Component(None, cff, [acfnprop, acfuprop])
    else:
        acfcomp = metarelate.Component(None, cff, [acfuprop])
    acfcomp.create_rdf(fu_p)
    return acfcomp


def get_grib2(fu_p):
    for gparam, cfname in grib_cf_map.GRIB2_TO_CF.iteritems():
        gribtemp = 'http://codes.wmo.int/grib2/codeflag/4.2/{d}-{c}-{i}'
        griburi = gribtemp.format(d=gparam.discipline,
                                  c=gparam.category,
                                  i=gparam.number)
        gpd = 'http://codes.wmo.int/def/grib2/parameter'
        agribprop = metarelate.StatementProperty(metarelate.Item(gpd),
                                                  metarelate.Item(griburi, gparam.number))
        gribmsg = 'http://codes.wmo.int/def/codeform/GRIB-message'
        agribcomp = metarelate.Component(None, gribmsg, [agribprop])
        agribcomp.create_rdf(fu_p)
        acfcomp = _cfname(fu_p, cfname)
        amap = metarelate.Mapping(None, agribcomp, acfcomp, editor=marqh,
                                  reason='"new mapping"',
                                  status='"Draft"')
        amap.create_rdf(fu_p)

def get_stash(fu_p):
    for stashmsi, cfname in um_cf_map.STASH_TO_CF.iteritems():
        stashuri = '{p}{c}'.format(p=pre['moStCon'], c=stashmsi)


        astashprop = metarelate.StatementProperty(metarelate.Item(Stash,'stash'),
                                                  metarelate.Item(stashuri, stashmsi))
        astashcomp = metarelate.Component(None, ppff, [astashprop])
        astashcomp.create_rdf(fu_p)

        acfcomp = _cfname(fu_p, cfname)
        amap = metarelate.Mapping(None, astashcomp, acfcomp, editor=marqh,
                                  reason='"new mapping"',
                                  status='"Draft"')
        amap.create_rdf(fu_p)


with FusekiServer() as fu_p:
    fu_p.load()
    # try:
    if True:
        get_stash(fu_p)
        get_grib2(fu_p)
    # except Exception, e:
    #     print e.message
    #     import pdb; pdb.set_trace()

    fu_p.save()

