#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$
import sys
import logging
from reportlab.platypus import PageBreak, Spacer
from flowables import *
import shlex

log = logging.getLogger('rst2pdf')
hdlr = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(levelname)s] %(filename)s L%(lineno)d %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.WARNING)

def parseRaw (data):
    '''Parse and process a simple DSL to handle creation of flowables.

    Supported (can add others on request):

    * PageBreak

    * Spacer width, height

    '''
    elements=[]
    lines=data.splitlines()
    for line in lines:
        lexer=shlex.shlex(line)
        lexer.whitespace+=','
        tokens=list(lexer)
        command=tokens[0]
        print tokens
        if command == 'PageBreak':
            if len(tokens)==1:
                print 'X1'
                elements.append(PageBreak())
            else:
                print 'X2'
                elements.append(MyPageBreak(tokens[1]))
        if command == 'Spacer':
            elements.append(Spacer(int(tokens[1]),int(tokens[2])))
    return elements

# Looks like this is not used anywhere now
#def depth (node):
#    if node.parent==None:
#        return 0
#    else:
#        return 1+depth(node.parent)
