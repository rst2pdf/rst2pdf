'''
A rst2pdf extension to implement something similar to sphinx's plantuml extension
(see http://pypi.python.org/pypi/sphinxcontrib-plantuml)

Therefore, stuff may be copied from that code.
Ergo:

    :copyright: Copyright 2010 by Yuya Nishihara <yuya@tcha.org>.
    :license: BSD, (he says see LICENSE but the file is not there ;-)

'''

from docutils import nodes
from docutils.parsers import rst
from docutils.parsers.rst import directives
import rst2pdf.genelements as genelements

class plantuml(nodes.General, nodes.Element):
    pass


class UmlDirective(rst.Directive):
    """Directive to insert PlantUML markup

    Example::

        .. uml::
           :alt: Alice and Bob

           Alice -> Bob: Hello
           Alice <- Bob: Hi
    """
    has_content = True
    option_spec = {'alt': directives.unchanged}

    def run(self):
        node = plantuml()
        node['uml'] = '\n'.join(self.content)
        node['alt'] = self.options.get('alt', None)
        return [node]


class UMLHandler(genelements.NodeHandler, plantuml):
    """Class to handle UML nodes"""

    def gather_elements(self, client, node, style):
        print "UML"
        return []

directives.register_directive("uml", UmlDirective)
