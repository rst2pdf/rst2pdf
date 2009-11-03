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
    ''' MetaHelper is designed to generically enable a few of the benefits of
        using metaclasses by encapsulating some of the complexity of setting
        them up.

        If a base class uses MetaHelper (by assigning __metaclass__ = MetaHelper),
        then that class (and its metaclass inheriting subclasses) can control
        class creation behavior by defining a couple of helper functions.

        1) A base class can define a _classpreinit function.  This function
           is called during __new__ processing of the class object itself,
           but only during subclass creation (not when the class defining
           the _classpreinit is itself created).

           The subclass object does not yet exist at the time _classpreinit
           is called.  _classpreinit accepts all the parameters of the
           __new__ function for the class itself (not the same as the __new__
           function for the instantiation of class objects!) and must return
           a tuple of the same objects.  A typical use of this would be to
           modify the class bases before class creation.

        2) Either a base class or a subclass can define a _classinit() function.
           This function will be called immediately after the actual class has
           been created, and can do whatever setup is required for the class.
           Note that every base class (but not every subclass) which uses
           MetaHelper MUST define _classinit, even if that definition is None.

         MetaHelper also places an attribute into each class created with it.
         _baseclass is set to None if this class has no superclasses which
         also use MetaHelper, or to the first such MetaHelper-using baseclass.
         _baseclass can be explicitly set inside the class definition, in
         which case MetaHelper will not override it.
    '''
    def __new__(clstype, name, bases, clsdict):
        # Our base class is the first base in the class definition which
        # uses MetaHelper, or None if no such base exists.
        base = ([x for x in bases if type(x) is MetaHelper] + [None])[0]

        # Only set our base into the class if it has not been explicitly
        # set
        clsdict.setdefault('_baseclass', base)

        # See if the base class definied a preinit function, and call it
        # if so.
        preinit = getattr(base, '_classpreinit', None)
        if preinit is not None:
            clstype, name, bases, clsdict = preinit(clstype, name, bases, clsdict)

        # Delegate the real work to type
        return type.__new__(clstype, name, bases, clsdict)

    def __init__(cls, name, bases, clsdict):
        # Let type build the class for us
        type.__init__(cls, name, bases, clsdict)
        # Call the class's initialization function if defined
        if cls._classinit is not None:
            cls._classinit()


class NodeHandler(object):
    ''' NodeHandler classes are used to dispatch
       to the correct class to handle some node class
       type, via a dispatchdict in the main class.
    '''
    __metaclass__ = MetaHelper

    @classmethod
    def _classpreinit(baseclass, clstype, name, bases, clsdict):
        # _classpreinit is called before the actual class is built
        # Perform triage on the class bases to separate actual
        # inheritable bases from the target docutils node classes
        # which we want to dispatch for.
        new_bases = []
        targets = []
        for target in bases:
            if target is not object:
                (targets, new_bases)[issubclass(target, baseclass)].append(target)
        clsdict['_targets'] = targets
        return clstype, name, tuple(new_bases), clsdict

    @classmethod
    def _classinit(cls):
        # _classinit() is called once the subclass has actually
        # been created.

        # For the base class, just add a dispatch dictionary
        if cls._baseclass is None:
            cls.dispatchdict = {}
            return

        # for subclasses, instantiate them, and then add
        # the class to the dispatch dictionary for each of its targets.
        self = cls()
        for target in cls._targets:
            if cls.dispatchdict.setdefault(target, self) is not self:
                t = repr(target)
                old = repr(cls.dispatchdict[target])
                new = repr(self)
                log.debug('Dispatch handler %s for node type %s overridden by %s' %
                    (old, t, new))

    @classmethod
    def findsubclass(cls, node):
        nodeclass = node.__class__
        log.debug("%s: %s", cls, nodeclass)
        log.debug("[%s]", nodeid(node))
        try:
            log.debug("%s: %s", cls, node)
        except (UnicodeDecodeError, UnicodeEncodeError):
            log.debug("%s: %r", cls, node)

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
