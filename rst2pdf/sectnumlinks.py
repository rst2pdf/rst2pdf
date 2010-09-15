import docutils

class SectNumFolder(docutils.nodes.SparseNodeVisitor):
    def __init__(self, document):
        docutils.nodes.SparseNodeVisitor.__init__(self, document)
        self.sectnums = {}

    def visit_generated(self, node):
        for i in node.parent.parent['ids']:
            self.sectnums[i]=node.astext().strip()

class SectRefExpander(docutils.nodes.SparseNodeVisitor):
    def __init__(self, document, sectnums):
        docutils.nodes.SparseNodeVisitor.__init__(self, document)
        self.sectnums = sectnums

    def visit_reference(self, node):
        if node.get('refid', None) in self.sectnums:
            node.children.insert(0,docutils.nodes.Text('%s '%self.sectnums[node.get('refid')]))
