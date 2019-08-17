# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: MIT

# Import all node handler modules here.
# The act of importing them wires them in.

from . import genelements  # noqa
from . import genpdftext  # noqa

# sphinxnodes needs these
from .genpdftext import FontHandler, HandleEmphasis, NodeHandler  # noqa

# createpdf needs this
nodehandlers = NodeHandler()
