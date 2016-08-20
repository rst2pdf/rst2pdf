from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
import docutils

class SectNumFolder(docutils.nodes.SparseNodeVisitor):
    def __init__(self, document):
        docutils.nodes.SparseNodeVisitor.__init__(self, document)
        self.sectnums = {}

    def visit_generated(self, node):
        for i in node.parent.parent['ids']:
            self.sectnums[i]=node.parent.astext().replace(u'\xa0\xa0\xa0',' ')

class SectRefExpander(docutils.nodes.SparseNodeVisitor):
    def __init__(self, document, sectnums):
        docutils.nodes.SparseNodeVisitor.__init__(self, document)
        self.sectnums = sectnums

    def visit_reference(self, node):
        if node.get('refid', None) in self.sectnums:
            node.children=[docutils.nodes.Text('%s '%self.sectnums[node.get('refid')])]
