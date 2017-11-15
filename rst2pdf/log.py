# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import str
import logging
import sys

logging.basicConfig(
    format='[%(levelname)s] %(filename)s:%(lineno)d %(message)s',
    level=logging.WARNING)

log = logging.getLogger('rst2pdf')

def nodeid(node):
    """Given a node, tries to return a way to see where it was in the
    source text"""
    fname='UNKNOWN'
    line='UNKNOWN'
    try:
        if node.line: line=str(node.line)
    except:
        pass
    try:
        if node.source: fname=str(node.source)
    except:
        pass
    return 'near line {} in file {}'.format(line, fname)