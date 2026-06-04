from docutils import nodes
from docutils.core import publish_doctree

from rst2pdf.createpdf import RstToPdf


def test_csv_table_accepts_comma_headers_with_custom_delimiter():
    RstToPdf()

    document = publish_doctree(
        '''
.. csv-table::
   :delim: |
   :header: "Header1", "Header2", "Header3"
   :widths: 46, 46, 8

   Some text here |  | Success
'''
    )

    assert not list(document.findall(nodes.system_message))
    assert 'Header1' in document.astext()
