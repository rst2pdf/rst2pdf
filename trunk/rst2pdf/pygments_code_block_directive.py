# -*- coding: utf-8 -*-
#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

# :Author: a Pygments author|contributor; Felix Wiemann; Guenter Milde
# :Date: $Date$
# :Copyright: This module has been placed in the public domain.
#
# This is a merge of `Using Pygments in ReST documents`_ from the pygments_
# documentation, and a `proof of concept`_ by Felix Wiemann.
#
# ========== ===========================================================
# 2007-06-01 Removed redundancy from class values.
# 2007-06-04 Merge of successive tokens of same type
#            (code taken from pygments.formatters.others).
# 2007-06-05 Separate docutils formatter script
#            Use pygments' CSS class names (like the html formatter)
#            allowing the use of pygments-produced style sheets.
# 2007-06-07 Merge in the formatting of the parsed tokens
#            (misnamed as docutils_formatter) as class DocutilsInterface
# 2007-06-08 Failsave implementation (fallback to a standard literal block
#            if pygments not found)
# ========== ===========================================================
#
# ::

"""Define and register a code-block directive using pygments"""


# Requirements
# ------------
# ::

import codecs
from docutils import nodes
from docutils.parsers.rst import directives

try:
    import pygments
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters.html import _get_ttype_class
except ImportError:
    pass

from log import log


# Customisation
# -------------
#
# Do not insert inline nodes for the following tokens.
# (You could add e.g. Token.Punctuation like ``['', 'p']``.) ::

unstyled_tokens = ['']


# DocutilsInterface
# -----------------
#
# This interface class combines code from
# pygments.formatters.html and pygments.formatters.others.
#
# It does not require anything of docutils and could also become a part of
# pygments::

class DocutilsInterface(object):
    """Parse `code` string and yield "classified" tokens.

    Arguments

      code     -- string of source code to parse
      language -- formal language the code is written in.

    Merge subsequent tokens of the same token-type.

    Yields the tokens as ``(ttype_class, value)`` tuples,
    where ttype_class is taken from pygments.token.STANDARD_TYPES and
    corresponds to the class argument used in pygments html output.

    """

    def __init__(self, code, language):
        self.code = code
        self.language = language

    def lex(self):
        # Get lexer for language (use text as fallback)
        try:
            if self.language and unicode(self.language).lower() <> 'none':
                lexer = get_lexer_by_name(self.language)
            else:
                lexer = get_lexer_by_name('text')
        except ValueError:
            log.info("no pygments lexer for %s, using 'text'" \
                % self.language)
            # what happens if pygment isn't present ?
            lexer = get_lexer_by_name('text')
        return pygments.lex(self.code, lexer)

    def join(self, tokens):
        """join subsequent tokens of same token-type
        """
        tokens = iter(tokens)
        (lasttype, lastval) = tokens.next()
        for ttype, value in tokens:
            if ttype is lasttype:
                lastval += value
            else:
                yield(lasttype, lastval)
                (lasttype, lastval) = (ttype, value)
        yield(lasttype, lastval)

    def __iter__(self):
        """parse code string and yield "clasified" tokens
        """
        try:
            tokens = self.lex()
        except IOError:
            log.info("Pygments lexer not found, using fallback")
            # TODO: write message to INFO
            yield ('', self.code)
            return

        for ttype, value in self.join(tokens):
            yield (_get_ttype_class(ttype), value)


# code_block_directive
# --------------------
# ::

def code_block_directive(name, arguments, options, content, lineno,
                       content_offset, block_text, state, state_machine):
    """Parse and classify content of a code_block."""
    if 'include' in options:
        try:
            content = codecs.open(options['include'], 'r', 'utf-8').read()
        except (IOError, UnicodeError): # no file or problem finding it or reading it
            log.error('Error reading file: "%s" L %s' % (options['include'], lineno))
            content = u''
        if content:
            # here we define the start-at and end-at options
            # so that limit is included in extraction
            # this is different than the start-after directive of docutils
            # (docutils/parsers/rst/directives/misc.py L73+)
            # which excludes the beginning
            # the reason is we want to be able to define a start-at like
            # def mymethod(self)
            # and have such a definition included
            #import pdb; pdb.set_trace()
            after_text = options.get('start-at', None)
            if after_text:
                # skip content in include_text before *and NOT incl.* a matching text
                after_index = content.find(after_text)
                if after_index < 0:
                    raise state_machine.reporter.severe('Problem with "start-at" option of "%s" '
                                      'code-block directive:\nText not found.' % options['start-at'])
                content = content[after_index:]

            after_text = options.get('start-after', None)
            if after_text:
                # skip content in include_text before *and incl.* a matching text
                print type(content), type(after_text)
                after_index = content.find(after_text)
                if after_index < 0:
                    raise state_machine.reporter.severe('Problem with "start-after" option of "%s" '
                                      'code-block directive:\nText not found.' % options['start-after'])
                content = content[after_index + len(after_text):]


            # same changes here for the same reason
            before_text = options.get('end-at', None)
            if before_text:
                # skip content in include_text after *and incl.* a matching text
                before_index = content.find(before_text)
                if before_index < 0:
                    raise state_machine.reporter.severe('Problem with "end-at" option of "%s" '
                                      'code-block directive:\nText not found.' % options['end-at'])
                content = content[:before_index + len(before_text)]

            before_text = options.get('end-before', None)
            if before_text:
                # skip content in include_text after *and NOT incl.* a matching text
                before_index = content.find(before_text)
                if before_index < 0:
                    raise state_machine.reporter.severe('Problem with "end-before" option of "%s" '
                                      'code-block directive:\nText not found.' % options['end-before'])
                content = content[:before_index]

    else:
        content = u'\n'.join(content)

    withln = "linenos" in options

    language = arguments[0]
    # create a literal block element and set class argument
    code_block = nodes.literal_block(classes=["code", language])

    if withln:
        lineno = 1
        total_lines = content.count('\n') + 1
        lnwidth = len(str(total_lines))
        fstr = "\n%%%dd " % lnwidth
        code_block += nodes.Text(fstr[1:] % lineno, fstr[1:] % lineno)

    # parse content with pygments and add to code_block element
    for cls, value in DocutilsInterface(content, language):
        if withln and "\n" in value:
            # Split on the "\n"s
            values = value.split("\n")
            # The first piece, pass as-is
            code_block += nodes.Text(values[0], values[0])
            # On the second and later pieces, insert \n and linenos
            linenos = range(lineno, lineno + len(values))
            for chunk, ln in zip(values, linenos)[1:]:
                if ln <= total_lines:
                    code_block += nodes.Text(fstr % ln, fstr % ln)
                    code_block += nodes.Text(chunk, chunk)
            lineno += len(values) - 1

        elif cls in unstyled_tokens:
            # insert as Text to decrease the verbosity of the output.
            code_block += nodes.Text(value, value)
        else:
            code_block += nodes.inline(value, value, classes=["pygments-" + cls])

    return [code_block]


# Register Directive
# ------------------
# ::

code_block_directive.arguments = (1, 0, 1)
code_block_directive.content = 1
code_block_directive.options = {'include': directives.unchanged_required,
                                'start-at': directives.unchanged_required,
                                'end-at': directives.unchanged_required,
                                'start-after': directives.unchanged_required,
                                'end-before': directives.unchanged_required,
                                'linenos': directives.unchanged,
                                }



# .. _doctutils: http://docutils.sf.net/
# .. _pygments: http://pygments.org/
# .. _Using Pygments in ReST documents: http://pygments.org/docs/rstdirective/
# .. _proof of concept:
#      http://article.gmane.org/gmane.text.docutils.user/3689
#
# Test output
# -----------
#
# If called from the command line, call the docutils publisher to render the
# input::

if __name__ == '__main__':
    from docutils.core import publish_cmdline, default_description
    description = "code-block directive test output" + default_description
    try:
        import locale
        locale.setlocale(locale.LC_ALL, '')
    except Exception:
        pass
    publish_cmdline(writer_name='pdf', description=description)
