=======
rst2pdf
=======

-----------------------------------------
Convert reStructuredText documents to PDF
-----------------------------------------

:Author: Chris Lamb <chris@chris-lamb.co.uk> for the Debian project
:Manual section: 1
:Manual group: text processing


SYNOPSIS
--------

rst2pdf [options] [input] [-o output]


DESCRIPTION
-----------

The usual way of creating PDF from reStructuredText (ReST) is by going through LaTeX.
The rst2pdf utility provides an alternative by producing PDF directly using the ReportLab
library.


OPTIONS
-------

-h, --help
                    Show this help message and exit

--config=FILE       Config file to use. Default=~/.rst2pdf/config

-o FILE, --output=FILE
                    Write the PDF to FILE

-s STYLESHEETS, --stylesheets=STYLESHEETS
                    A comma-separated list of custom stylesheets.
                    Default=""

--stylesheet-path=FOLDERLIST
                    A colon-separated list of folders to search for
                    stylesheets. Default=""

-c, --compressed
                    Create a compressed PDF. Default=False

--print-stylesheet
                    Print the default stylesheet and exit

--font-folder=FOLDER
                    Search this folder for fonts. (Deprecated)

--font-path=FOLDERLIST
                    A colon-separated list of folders to search for fonts.
                    Default=""

--baseurl=URL
                    The base URL for relative URLs.

-l LANG, --language=LANG
                    Language to be used for hyphenation and docutils localization.
                    Default=None

--header=HEADER
                    Page header if not specified in the document.

--footer=FOOTER
                    Page footer if not specified in the document.

--section-header-depth=N
                    Sections up to this dept will be used in the header
                    and footer's replacement of ###Section###. Default=2

--smart-quotes=VALUE  Try to convert ASCII quotes, ellipsis and dashes to
                      the typographically correct equivalent. Default=0

The possible values are:

0. Suppress all transformations. (Do nothing.)

1. Performs default SmartyPants transformations: quotes (including backticks-style), em-dashes, and ellipses. "--" (dash dash) is used to signify an em-dash; there is no support for en-dashes.

2. Same as --smart-quotes=1, except that it uses the old-school typewriter shorthand for dashes: "--" (dash dash) for en-dashes, "---" (dash dash dash) for em-dashes.

3. Same as --smart-quotes=2, but inverts the shorthand for dashes: "--" (dash dash) for em-dashes, and "---" (dash dash dash) for en-dashes.

--fit-literal-mode=MODE
                    What to do when a literal is too wide.
                    One of error,overflow,shrink,truncate.
                    Default="shrink"

--fit-background-mode=MODE
                        How to fit the background image to the page. One of
                        scale, scale_width or center. Default="center"

--inline-links
                    Shows target between parenthesis instead of active link


--repeat-table-rows
                    Repeats header row for each splitted table

--raw-html          Support embeddig raw HTML. Default: False

-q, --quiet
                    Print less information.

-v, --verbose
                    Print debug information.

--very-verbose
                    Print even more debug information.

--version
                    Print version number and exit.

--no-footnote-backlinks   Disable footnote backlinks. Default: False

--inline-footnotes    Show footnotes inline. Default: True

--default-dpi=NUMBER   DPI for objects sized in pixels. Default=300

--show-frame-boundary   Show frame borders (only useful for debugging).
                        Default=False

--disable-splittables
                        Don't use splittable flowables in some elements. Only
                        try this if you can't process a document any other
                        way.

-b LEVEL, --break-level=LEVEL
                    Maximum section level that starts in a new page. Default: 0

--first-page-on-right When using double sided pages, the first page will start
                      on the right hand side. (Book Style)

--blank-first-page    Add a blank page at the beginning of the document.

--break-side=VALUE    How section breaks work. Can be "even", and sections
                      start in an even page,"odd", and sections start in odd
                      pages, or "any" and sections start in the next page,be
                      it even or odd. See also the -b option.

--date-invariant      Don't store the current date in the PDF. Useful mainly
                      for the test suite, where we don't want the PDFs to
                      change.

-e EXTENSIONS         Alias for --extension-module

--extension-module=EXTENSIONS
                        Add a helper extension module to this invocation of
                        rst2pdf (module must end in .py and be on the python
                        path)

--custom-cover=FILE
                        Template file used for the cover page. Default:
                        cover.tmpl

--use-floating-images
                        Makes images with :align: attribute work more like in
                        rst2html. Default: False

--use-numbered-links  When using numbered sections, adds the numbers to all
                      links referring to the section headers. Default: False

--strip-elements-with-class=CLASS
                      Remove elements with this CLASS from the output. Can
                      be used multiple times.

--record-dependencies=FILE
                      Write output file dependencies to FILE.


EXAMPLES
--------

$ rst2pdf rest.txt -o out.pdf

Produce an out.pdf file which is a PDF version of the ReST document rest.txt.
