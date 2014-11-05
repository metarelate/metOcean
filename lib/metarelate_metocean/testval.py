from inspect import getmembers, isfunction

from metarelate import careful_update
import metarelate.fuseki as fu

import validation

with fu.FusekiServer() as fu_p:

    failures = {}

    vtests = [o[0] for o in getmembers(validation) if isfunction(o[1]) and not o[0].startswith('_')]

    for vtest in vtests:
        res = validation.__dict__[vtest].__call__(fu_p)
        careful_update(failures, res)

print failures

