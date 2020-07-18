# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

# Import all node handler modules here.
# The act of importing them wires them in.

from . import genelements  # noqa
from . import genpdftext  # noqa

# sphinxnodes needs these
from .genpdftext import NodeHandler, FontHandler, HandleEmphasis  # noqa

# createpdf needs this
nodehandlers = NodeHandler()
