import metarelate
from metarelate.prefixes import Prefixes
from metarelate.fuseki import FusekiServer

from iris.fileformats import um_cf_map
from iris.fileformats.grib import _grib_cf_map as grib_cf_map

ppff = 'http://reference.metoffice.gov.uk/um/f3/UMField'
Stash = 'http://reference.metoffice.gov.uk/um/c4/stash/Stash'
fci = 'http://reference.metoffice.gov.uk/um/f3/lbfc'

cff = 'http://def.scitools.org.uk/cfmodel/Field'
cfsn = 'http://def.scitools.org.uk/cfmodel/standard_name'
cfln = 'http://def.scitools.org.uk/cfmodel/long_name'
cfun = 'http://def.scitools.org.uk/cfmodel/units'
cfpoints = 'http://def.scitools.org.uk/cfmodel/points'
cfdimcoord = 'http://def.scitools.org.uk/cfmodel/dim_coord'

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
    return acfcomp

def get_grib1_mo(fu_p):
    for g1l, cfname in grib_cf_map.GRIB1_LOCAL_TO_CF.iteritems():
        pass

def dimcoord(fu_p, name, units, value):
    sname = '{p}{c}'.format(p=pre['cfnames'], c=name)
    acfnprop = metarelate.StatementProperty(metarelate.Item(cfsn),
                                            metarelate.Item(sname))
    acfuprop = metarelate.StatementProperty(metarelate.Item(cfun),
                                            metarelate.Item(units))
    acfvprop = metarelate.StatementProperty(metarelate.Item(cfpoints),
                                            metarelate.Item(value))
    acfcomp = metarelate.Component(None, cff, [acfnprop, acfuprop, acfvprop])
    acfcomp.create_rdf(fu_p)
    stp = metarelate.StatementProperty(metarelate.Item(cfdimcoord),
                                       acfcomp)
    return stp

def get_grib1_mo_constrained(fu_p):
    for g1l, cfname_h in grib_cf_map.GRIB1_LOCAL_TO_CF_CONSTRAINED.iteritems():
        gribtemp = 'http://reference.metoffice.gov.uk/grib/grib1/parameter/{v}-{c}-{i}'
        griburi = gribtemp.format(v=g1l.t2version,
                                  c=g1l.centre,
                                  i=g1l.iParam)
        gpd = 'http://codes.wmo.int/def/grib1/parameter'
        agribprop = metarelate.StatementProperty(metarelate.Item(gpd),
                                                  metarelate.Item(griburi, g1l.iParam))
        gribmsg = 'http://codes.wmo.int/def/codeform/GRIB-message'
        agribcomp = metarelate.Component(None, gribmsg, [agribprop])
        agribcomp.create_rdf(fu_p)
        acfcomp = _cfname(fu_p, cfname_h[0])
        hn = dimcoord(fu_p, cfname_h[1].standard_name,
                      cfname_h[1].units, '{}'.format(cfname_h[1].points))
        acfcomp.properties.append(hn)
        acfcomp.create_rdf(fu_p)
        amap = metarelate.Mapping(None, agribcomp, acfcomp, editor=marqh,
                                  reason='"new mapping"',
                                  status='"Draft"', invertible='"True"')
        amap.create_rdf(fu_p)
        

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
        acfcomp.create_rdf(fu_p)
        inv = '"False"'
        if cfname in grib_cf_map.CF_TO_GRIB2 and \
            grib_cf_map.CF_TO_GRIB2[cfname] == gparam:
            inv = '"True"'
        amap = metarelate.Mapping(None, agribcomp, acfcomp, editor=marqh,
                                  reason='"new mapping"',
                                  status='"Draft"', invertible=inv)
        amap.create_rdf(fu_p)
    for cfname, gparam in grib_cf_map.CF_TO_GRIB2.iteritems():
        if not (gparam in grib_cf_map.GRIB2_TO_CF and \
            grib_cf_map.GRIB2_TO_CF[gparam] == cfname):
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
            acfcomp.create_rdf(fu_p)
            inv = '"False"'
            amap = metarelate.Mapping(None, acfcomp, agribcomp, editor=marqh,
                                      reason='"new mapping"',
                                      status='"Draft"', invertible=inv)
            amap.create_rdf(fu_p)


def get_stash(fu_p):
    for stashmsi, cfname in um_cf_map.STASH_TO_CF.iteritems():
        stashuri = '{p}{c}'.format(p=pre['moStCon'], c=stashmsi)


        astashprop = metarelate.StatementProperty(metarelate.Item(Stash,'stash'),
                                                  metarelate.Item(stashuri, stashmsi))
        astashcomp = metarelate.Component(None, ppff, [astashprop])
        astashcomp.create_rdf(fu_p)

        acfcomp = _cfname(fu_p, cfname)
        acfcomp.create_rdf(fu_p)

        amap = metarelate.Mapping(None, astashcomp, acfcomp, editor=marqh,
                                  reason='"new mapping"',
                                  status='"Draft"')
        amap.create_rdf(fu_p)

def get_fc(fu_p):
    for fc, cfname in um_cf_map.LBFC_TO_CF.iteritems():
        fcuri = 'http://reference.metoffice.gov.uk/um/fieldcode/{}'.format(fc)
        afc = metarelate.StatementProperty(metarelate.Item(fci),
                                                  metarelate.Item(fcuri))
        afccomp = metarelate.Component(None, ppff, [afc])
        afccomp.create_rdf(fu_p)

        acfcomp = _cfname(fu_p, cfname)
        acfcomp.create_rdf(fu_p)
        source = afccomp
        target = acfcomp
        inv = '"False"'
        if cfname in um_cf_map.CF_TO_LBFC:
            if um_cf_map.CF_TO_LBFC[cfname] == fc:
                inv = '"True"'

        amap = metarelate.Mapping(None, source, target, editor=marqh,
                                  reason='"new mapping"',
                                  status='"Draft"', invertible=inv)
        amap.create_rdf(fu_p)
    for cfname, fc in um_cf_map.CF_TO_LBFC.iteritems():
        if fc not in um_cf_map.LBFC_TO_CF:
            fcuri = 'http://reference.metoffice.gov.uk/um/fieldcode/{}'.format(fc)
            afc = metarelate.StatementProperty(metarelate.Item(fci),
                                                      metarelate.Item(fcuri))
            afccomp = metarelate.Component(None, ppff, [afc])
            afccomp.create_rdf(fu_p)

            acfcomp = _cfname(fu_p, cfname)
            acfcomp.create_rdf(fu_p)
            source = acfcomp
            target = afccomp
            inv = '"False"'

            amap = metarelate.Mapping(None, source, target, editor=marqh,
                                      reason='"new mapping"',
                                      status='"Draft"', invertible=inv)
            amap.create_rdf(fu_p)

with FusekiServer() as fu_p:
    fu_p.load()
    # try:
    if True:
        get_stash(fu_p)
        get_fc(fu_p)
        get_grib2(fu_p)
        get_grib1_mo_constrained(fu_p)
    # except Exception, e:
    #     print e.message
    #     import pdb; pdb.set_trace()

    #fu_p.save()

