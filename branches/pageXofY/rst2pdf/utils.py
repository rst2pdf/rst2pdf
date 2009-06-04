# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms
#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

import shlex

from reportlab.platypus import Spacer

from flowables import *


def parseRaw (data):
    """Parse and process a simple DSL to handle creation of flowables.

    Supported (can add others on request):

    * PageBreak

    * Spacer width, height

    """
    elements = []
    lines = data.splitlines()
    for line in lines:
        lexer = shlex.shlex(line)
        lexer.whitespace += ','
        tokens = list(lexer)
        command = tokens[0]
        if command == 'PageBreak':
            if len(tokens) == 1:
                elements.append(MyPageBreak())
            else:
                elements.append(MyPageBreak(tokens[1]))
        if command == 'Spacer':
            elements.append(Spacer(int(tokens[1]), int(tokens[2])))
        if command == 'Transition':
            elements.append(Transition(*tokens[1:]))
    return elements


# Looks like this is not used anywhere now:
# def depth(node):
#    if node.parent == None:
#        return 0
#    else:
#        return 1 + depth(node.parent)
