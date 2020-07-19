# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

import logging

log = logging.getLogger('rst2pdf')
_fmt = logging.Formatter('[%(levelname)s] %(filename)s:%(lineno)d %(message)s')
_hdlr = logging.StreamHandler()
_hdlr.setFormatter(_fmt)
log.addHandler(_hdlr)
log.setLevel(logging.WARNING)


def nodeid(node):
    """Given a node, tries to return a way to see where it was in the
    source text"""
    fname = 'UNKNOWN'
    line = 'UNKNOWN'

    try:
        if node.line:
            line = str(node.line)
    except Exception:
        pass

    try:
        if node.source:
            fname = str(node.source)
    except Exception:
        pass

    return 'near line %s in file %s' % (line, fname)
