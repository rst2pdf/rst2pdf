# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms
#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

import shlex

from reportlab.platypus import Spacer

from flowables import *
import flowables
from styles import adjustUnits
from log import log

def parseRaw(data):
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
        elif command == 'EvenPageBreak':
            if len(tokens) == 1:
                elements.append(MyPageBreak(breakTo='even'))
            else:
                elements.append(MyPageBreak(tokens[1],breakTo='even'))
        elif command == 'OddPageBreak':
            if len(tokens) == 1:
                elements.append(MyPageBreak(breakTo='odd'))
            else:
                elements.append(MyPageBreak(tokens[1],breakTo='odd'))
        elif command == 'Spacer':
            elements.append(Spacer(adjustUnits(tokens[1]), 
                adjustUnits(tokens[2])))
        elif command == 'Transition':
            elements.append(Transition(*tokens[1:]))
        elif command == 'SetPageCounter':
            elements.append(flowables.PageCounter(*tokens[1:]))
        else:
            log.error('Unknown command %s in raw pdf directive'%command)
    return elements


# Looks like this is not used anywhere now:
# def depth(node):
#    if node.parent == None:
#        return 0
#    else:
#        return 1 + depth(node.parent)
