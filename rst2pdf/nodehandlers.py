# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms
# $URL$
# $Date$
# $Revision$

# Import all node handler modules here.
# The act of importing them wires them in.
from rst2pdf import genelements
from rst2pdf import genpdftext

# sphinxnodes needs these
from rst2pdf.genpdftext import NodeHandler, FontHandler, HandleEmphasis

# createpdf needs this
nodehandlers = NodeHandler()
