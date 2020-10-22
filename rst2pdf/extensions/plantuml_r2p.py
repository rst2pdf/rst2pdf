'''
A rst2pdf extension to implement something similar to sphinx's plantuml extension
(see http://pypi.python.org/pypi/sphinxcontrib-plantuml)

Therefore, stuff may be copied from that code.
Ergo:

    :copyright: Copyright 2010 by Yuya Nishihara <yuya@tcha.org>.
    :license: BSD, (he says see LICENSE but the file is not there ;-)

'''

import errno
import subprocess
import tempfile

from docutils import nodes
from docutils.parsers import rst
from docutils.parsers.rst import directives

import rst2pdf.genelements as genelements
from rst2pdf.image import MyImage
from rst2pdf.styles import adjustUnits


class plantuml(nodes.General, nodes.Element):
    pass


class UmlDirective(rst.Directive):
    """Directive to insert PlantUML markup

    Example::

        .. uml::
           :alt: Alice and Bob

           Alice -> Bob: Hello
           Alice <- Bob: Hi


    You can use a :format: option to change between SVG and PNG diagrams, however,
    the SVG plantuml generates doesn't look very good to me.

    Also, :width: and :height: are supported as per the image directive.
    """

    has_content = True
    option_spec = {
        'alt': directives.unchanged,
        'format': directives.unchanged,
        'width': directives.length_or_unitless,
        'height': directives.length_or_unitless,
    }

    def run(self):
        node = plantuml()
        node['uml'] = '\n'.join(self.content)
        node['alt'] = self.options.get('alt', None)
        node['format'] = self.options.get('format', 'png')
        node['width'] = self.options.get('width', None)
        node['height'] = self.options.get('height', None)
        return [node]


class PlantUmlError(Exception):
    pass


class UMLHandler(genelements.NodeHandler, plantuml):
    """Class to handle UML nodes"""

    def gather_elements(self, client, node, style):
        # Create image calling plantuml
        tfile = tempfile.NamedTemporaryFile(
            dir='.', delete=False, suffix='.' + node['format']
        )
        args = 'plantuml -pipe -charset utf-8'
        if node['format'].lower() == 'svg':
            args += ' -tsvg'
        client.to_unlink.append(tfile.name)
        try:
            p = subprocess.Popen(
                args.split(),
                stdout=tfile,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as err:
            if err.errno != errno.ENOENT:
                raise
            raise PlantUmlError(
                'plantuml command %r cannot be run' % self.builder.config.plantuml
            )
        serr = p.communicate(node['uml'].encode('utf-8'))[1]
        if p.returncode != 0:
            raise PlantUmlError('error while running plantuml\n\n' + serr)

        # Convert width and height if necessary
        w = node['width']
        if w is not None:
            w = adjustUnits(w)

        h = node['height']
        if h is not None:
            h = adjustUnits(h)

        # Add Image node with the right image
        return [MyImage(tfile.name, client=client, width=w, height=h)]


directives.register_directive("uml", UmlDirective)
