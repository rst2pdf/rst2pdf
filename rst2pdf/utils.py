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
from log import log, nodeid

import inspect

class MetaHelper(type):
    '''  MetaHelper is to simplify the use of metaclasses for one useful case.
         Whenever a class which uses MetaHelper as its metaclass is compiled,
         after compilation, that class's _classinit() function will be called.
         _classinit() will be passed a base class parameter which is the
         superclass which also uses MetaHelper as its metaclass, or None if
         no such superclass exists. 
    '''
    def __new__(cls, name, bases, clsdict):
        base = ([x for x in bases if type(x) is MetaHelper] + [None])[0]
        clsdict.setdefault('_baseclass', base)
        preinit = getattr(base, '_classpreinit', None)
        if preinit is not None:
            cls, name, bases, clsdict = preinit(cls, name, bases, clsdict)
        return type.__new__(cls, name, bases, clsdict)

    def __init__(cls, name, bases, clsdict):
        type.__init__(cls, name, bases, clsdict)
        if cls._classinit is not None:
            cls._classinit()


class NodeHandler(object):
    ''' NodeHandler classes are used to dispatch
       to the correct class to handle some node class
       type, via a dispatchdict in the main class.
    '''
    __metaclass__ = MetaHelper

    @classmethod
    def _classpreinit(baseclass, cls, name, bases, clsdict):
        new_bases = []
        targets = []
        for target in bases:
            if target is not object:
                (targets, new_bases)[issubclass(target, baseclass)].append(target)
        clsdict['_targets'] = targets
        return cls, name, tuple(new_bases), clsdict

    @classmethod
    def _classinit(cls):
        if cls._baseclass is None:
            cls.dispatchdict = {}
            return
        self = cls()
        for target in cls._targets:
            if cls.dispatchdict.setdefault(target, self) is not self:
                t = repr(target)
                old = repr(cls.dispatchdict[target])
                new = repr(self)
                raise ValueError("Multiple handlers for %s: %s and %s" % (t, old, new))

    @classmethod
    def findsubclass(cls, node):
        nodeclass = node.__class__
        log.debug("%s: %s", (cls, nodeclass))
        log.debug("[%s]", nodeid(node))
        try:
            log.debug("%s: %s", (cls, node))
        except (UnicodeDecodeError, UnicodeEncodeError):
            log.debug("%s: %r", (cls, node))

        # Dispatch to the first matching class in the MRO

        dispatchdict = cls.dispatchdict
        for baseclass in inspect.getmro(nodeclass):
            self = dispatchdict.get(baseclass)
            if self is not None:
                break
        else:
            self = cls.default_dispatch
        return self

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
