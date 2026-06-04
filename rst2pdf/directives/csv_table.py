# -*- coding: utf-8 -*-

"""Custom csv-table directive that supports comma-separated headers
with custom delimiters for backward compatibility.

In the standard docutils csv-table directive, when a custom delimiter
is specified via :delim:, ALL fields including headers must use that
delimiter. This directive wraps the standard csv-table to automatically
convert comma-separated headers to use the custom delimiter, restoring
the pre-docutils-0.18 behavior.
"""

from docutils.parsers.rst.directives.tables import CSVTable


class BackwardCompatibleCSVTable(CSVTable):
    """
    A csv-table directive that accepts comma-separated headers even when
    a custom delimiter is specified.

    When :delim: is set to a non-comma value, this directive automatically
    converts commas in the :header: option to the custom delimiter.
    """

    def run(self):
        # Check if a custom (non-comma) delimiter is set
        delim = self.options.get('delim', None)
        if delim and delim != ',':
            header = self.options.get('header', None)
            if header and ',' in header:
                # The header uses commas but the delimiter is custom.
                # Replace commas with the custom delimiter.
                self.options['header'] = header.replace(',', delim)

        return super().run()
