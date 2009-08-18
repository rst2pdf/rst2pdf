# -*- coding: utf-8 -*-
"""
      Sphinx rst2pdf builder extension
      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

      Usage:
      1. Copy this file to your Sphinx project directory.
      2. In conf.py file uncomment this line:
         #sys.path.append(os.path.abspath('.'))
      3. In conf.py add 'pdfbuilder' element to 'extensions' list:
         extensions = ['pdfbuilder']
      4. Modify your Makefile or run it with:
         $ sphinx-build -d_build/doctrees -bpdf . _build/pdf

    :copyright: Copyright 2009 Roberto Alsina, Wojtek Walczak
    :license: BSD, see LICENSE for details.
"""


import parser
import re
import sys
from os import path

from StringIO import StringIO
from rst2pdf import createpdf
from rst2pdf import pygments_code_block_directive
from pygments.lexers import get_lexer_by_name, guess_lexer

from docutils import writers
from docutils import nodes
from docutils import languages
from docutils.transforms.parts import Contents
from docutils.io import FileOutput
import docutils.core

from sphinx import addnodes
from sphinx.builders import Builder
from sphinx.util.console import darkgreen
from sphinx.util import SEP
from sphinx.util import ustrftime, texescape
import rst2pdf.log
import logging
from pprint import pprint


class PDFBuilder(Builder):
    name = 'pdf'
    out_suffix = '.pdf'

    def init(self):
        self.docnames = []
        self.document_data = []

    def write(self, *ignored):
        
        self.init_document_data()
        
        if self.config.pdf_verbosity > 1:
            rst2pdf.log.log.setLevel(logging.DEBUG)
        elif self.config.pdf_verbosity > 0:
            rst2pdf.log.log.setLevel(logging.INFO)
    
        for entry in self.document_data:
            docname, targetname, title, author = entry[:4]
            self.info("processing " + targetname + "... ", nonl=1)
            docwriter = PDFWriter(self,
                            stylesheets=self.config.pdf_stylesheets,
                            language=self.config.pdf_language,
                            breaklevel=self.config.pdf_break_level,
                            fontpath=self.config.pdf_font_path,
                            fitmode=self.config.pdf_fit_mode,
                            compressed=self.config.pdf_compressed,
                            inline_footnotes=self.config.pdf_inline_footnotes,
                            )
            tgt_file = path.join(self.outdir, targetname + self.out_suffix)
            destination = FileOutput(destination_path=tgt_file, encoding='utf-8')
            doctree = self.assemble_doctree(docname,title,author)
            self.info("done")
            self.info("writing " + targetname + "... ", nonl=1)
            docwriter.write(doctree, destination)
            self.info("done")
        
    def init_document_data(self):
        preliminary_document_data = map(list, self.config.pdf_documents)
        if not preliminary_document_data:
            self.warn('no "pdf_documents" config value found; no documents '
                      'will be written')
            return
        # assign subdirs to titles
        self.titles = []
        for entry in preliminary_document_data:
            docname = entry[0]
            if docname not in self.env.all_docs:
                self.warn('"pdf_documents" config value references unknown '
                          'document %s' % docname)
                continue
            self.document_data.append(entry)
            if docname.endswith(SEP+'index'):
                docname = docname[:-5]
            self.titles.append((docname, entry[2]))

    def assemble_doctree(self, docname, title, author):
        # Page transitions
        output='.. raw:: pdf\n\n    PageBreak\n\n'
        pb=docutils.core.publish_doctree(output)[0]
        output='.. raw:: pdf\n\n    PageBreak oneColumn\n\n'
        pb_oneColumn=docutils.core.publish_doctree(output)[0]
        output='.. raw:: pdf\n\n    PageBreak cutePage\n\n'
        pb_cutePage=docutils.core.publish_doctree(output)[0]
        output='.. raw:: pdf\n\n    PageBreak twoColumn\n\n'
        pb_twoColumn=docutils.core.publish_doctree(output)[0]
        
        self.docnames = set([docname])
        self.info(darkgreen(docname) + " ", nonl=1)
        def process_tree(docname, tree):
            tree = tree.deepcopy()
            for toctreenode in tree.traverse(addnodes.toctree):
                newnodes = []
                includefiles = map(str, toctreenode['includefiles'])
                for includefile in includefiles:
                    try:
                        self.info(darkgreen(includefile) + " ", nonl=1)
                        subtree = process_tree(includefile,
                        self.env.get_doctree(includefile))
                        self.docnames.add(includefile)
                    except Exception:
                        self.warn('%s: toctree contains ref to nonexisting file %r'\
                                                     % (docname, includefile))
                    else:
                        sof = addnodes.start_of_file(docname=includefile)
                        sof.children = subtree.children
                        newnodes.append(sof)
                toctreenode.parent.replace(toctreenode, newnodes)
            return tree

        tree = self.env.get_doctree(docname)
        
        tree = process_tree(docname, tree)

        if self.config.language:
            langmod = languages.get_language(self.config.language[:2])
        else:
            langmod = languages.get_language('en')
            
        if self.config.pdf_use_index:
            # Add index at the end of the document
            genindex = self.env.create_index(self)
            _pb,index_nodes=genindex_nodes(genindex)
            tree.append(_pb)
            tree.append(index_nodes)

        # This is stolen from the HTML builder
        #moduleindex = self.env.domaindata['py']['modules']
        if self.config.pdf_use_modindex and self.env.modules:
            modules = sorted(((mn, ('#module-' + mn, sy, pl, dep)) 
                for (mn, (fn, sy, pl, dep)) in self.env.modules.iteritems()),
                key=lambda x: x[0].lower())
            # collect all platforms
            platforms = set()
            letters = []
            pmn = ''
            fl = '' # first letter
            modindexentries = []
            num_toplevels = 0
            num_collapsables = 0
            cg = 0 # collapse group
            for mn, (fn, sy, pl, dep) in modules:
                pl = pl and pl.split(', ') or []
                platforms.update(pl)
                ignore = self.env.config['modindex_common_prefix']
                ignore = sorted(ignore, key=len, reverse=True)
                for i in ignore:
                    if mn.startswith(i):
                        mn = mn[len(i):]
                        stripped = i
                        break
                else:
                    stripped = ''

                if fl != mn[0].lower() and mn[0] != '_':
                    # heading
                    letter = mn[0].upper()
                    if letter not in letters:
                        modindexentries.append(['', False, 0, False,
                                                letter, '', [], False, ''])
                        letters.append(letter)
                tn = mn.split('.')[0]
                if tn != mn:
                    # submodule
                    if pmn == tn:
                        # first submodule - make parent collapsable
                        modindexentries[-1][1] = True
                        num_collapsables += 1
                    elif not pmn.startswith(tn):
                        # submodule without parent in list, add dummy entry
                        cg += 1
                        modindexentries.append([tn, True, cg, False, '', '',
                                                [], False, stripped])
                else:
                    num_toplevels += 1
                    cg += 1
                modindexentries.append([mn, False, cg, (tn != mn), fn, sy, pl,
                                        dep, stripped])
                pmn = mn
                fl = mn[0].lower()
            platforms = sorted(platforms)
            # As some parts of the module names may have been stripped, those
            # names have changed, thus it is necessary to sort the entries.
            if ignore:
                def sorthelper(entry):
                    name = entry[0]
                    if name == '':
                        # heading
                        name = entry[4]
                    return name.lower()

                modindexentries.sort(key=sorthelper)
                letters.sort()

            # Now, let's try to do the same thing
            # modindex.html does, more or less
            
            output=['DUMMY','=====','',
                    '.. raw:: pdf\n\n    PageBreak twoColumn\n\n.. _modindex:\n\n']
            t=_('Global Module Index')
            t+='\n'+'='*len(t)+'\n'
            output.append(t)
            for modname, collapse, cgroup, indent,\
                fname, synops, pform, dep, stripped in modindexentries:
                if not modname: # A letter
                    output.append('.. cssclass:: heading4\n\n%s\n\n'%fname)
                else: # A module
                    if fname:
                        output.append('`%s <%s>`_'%(stripped+modname,fname))
                        if pform and pform[0]:
                            output[-1]+='*(%s)*'%' '.join(pform)
                        if synops:
                            output[-1]+=', *%s*'%synops
                        if dep:
                            output[-1]+=' **%s**'%_('Deprecated')
                output.append('')
            
            dt = docutils.core.publish_doctree('\n'.join(output))
            tree.append(pb_twoColumn)
            tree.extend(dt[1:])
            
            
        # Generate Contents topic manually
        contents=nodes.topic(classes=['contents'])
        contents+=nodes.title('')
        contents[0]+=nodes.Text( langmod.labels['contents'])
        contents['ids']=['Contents']
        pending=nodes.topic()
        contents.append(pending)
        pending.details={}
        #tree.insert(0,pb_cutePage)
        tree.insert(0,contents)
        contTrans=PDFContents(tree)
        contTrans.startnode=pending
        contTrans.apply()

        if self.config.pdf_use_coverpage:
            # Generate cover page
            spacer=docutils.core.publish_doctree('.. raw:: pdf\n\n    Spacer 0 3cm\n\n')[0]
            doctitle=nodes.title()
            doctitle.append(nodes.Text(title))
            docsubtitle=nodes.subtitle()
            docsubtitle.append(nodes.Text('%s %s'%(_('version'),self.config.version)))
            authornode=nodes.paragraph()
            authornode.append(nodes.Text(author))
            authornode['classes']=['author']
            date=nodes.paragraph()
            date.append(nodes.Text(ustrftime(self.config.today_fmt or _('%B %d, %Y'))))
            date['classes']=['author']
            tree.insert(0,pb_cutePage)
            tree.insert(0,pb)
            tree.insert(0,date)
            tree.insert(0,spacer)
            tree.insert(0,authornode)
            tree.insert(0,spacer)
            tree.insert(0,docsubtitle)
            tree.insert(0,doctitle)
        
        for pendingnode in tree.traverse(addnodes.pending_xref):
            # This needs work, need to keep track of all targets
            # so I don't replace and create hanging refs, which
            # crash
            if pendingnode['reftarget'] == 'genindex'\
                and self.config.pdf_use_index:
                pendingnode.replace_self(nodes.reference(text=pendingnode.astext(),
                    refuri=pendingnode['reftarget']))
            if pendingnode['reftarget'] == 'modindex'\
                and self.config.pdf_use_modindex:
                pendingnode.replace_self(nodes.reference(text=pendingnode.astext(),
                    refuri=pendingnode['reftarget']))
            else:
                pass
        return tree
    

    def get_target_uri(self, docname, typ=None):
        return ''

    def get_outdated_docs(self):
        for docname in self.env.found_docs:
            if docname not in self.env.all_docs:
                yield docname
                continue
            targetname = self.env.doc2path(docname, self.outdir, self.out_suffix)
            try:
                targetmtime = path.getmtime(targetname)
            except Exception:
                targetmtime = 0
            try:
                srcmtime = path.getmtime(self.env.doc2path(docname))
                if srcmtime > targetmtime:
                    yield docname
            except EnvironmentError:
                # source doesn't exist anymore
                pass

def genindex_nodes(genindexentries):
    indexlabel = _('Index')
    indexunder = '='*len(indexlabel)
    output=['DUMMY','=====','','.. raw:: pdf\n\n    PageBreak twoColumn\n\n.. _genindex:\n\n',indexlabel,indexunder,'']

    for key, entries in genindexentries:
        output.append('.. cssclass:: heading4\n\n%s\n\n'%key) # initial
        for entryname, (links, subitems) in entries:
            if links:
                output.append('`%s <%s>`_'%(entryname,links[0]))
                for i,link in enumerate(links[1:]):
                    output[-1]+=(' `[%s] <%s>`_ '%(i+1,link))
                output.append('')
            else:
                output.append(entryname)
            if subitems:
                for subentryname, subentrylinks in subitems:
                    output.append('    `%s <%s>`_'%(subentryname,subentrylinks[0]))
                    for i,link in enumerate(subentrylinks[1:]):
                        output[-1]+=(' `[%s] <%s>`_ '%(i+1,link))
                    output.append('')

    doctree = docutils.core.publish_doctree('\n'.join(output))
    return doctree[0][1],doctree[1]


class PDFContents(Contents):
    
    def build_contents(self, node, level=0):
        level += 1
        sections=[]
        for sect in node:
            if isinstance(sect,addnodes.start_of_file):
                for sect2 in sect:
                    if isinstance(sect2,nodes.section):
                        sections.append(sect2)
            elif isinstance(sect, nodes.section):
                sections.append(sect)
        #sections = [sect for sect in node if isinstance(sect, nodes.section)]
        entries = []
        autonum = 0
        depth = self.startnode.details.get('depth', sys.maxint)
        for section in sections:
            title = section[0]
            auto = title.get('auto')    # May be set by SectNum.
            entrytext = self.copy_and_filter(title)
            reference = nodes.reference('', '', refid=section['ids'][0],
                                        *entrytext)
            ref_id = self.document.set_id(reference)
            entry = nodes.paragraph('', '', reference)
            item = nodes.list_item('', entry)
            if ( self.backlinks in ('entry', 'top')
                 and title.next_node(nodes.reference) is None):
                if self.backlinks == 'entry':
                    title['refid'] = ref_id
                elif self.backlinks == 'top':
                    title['refid'] = self.toc_id
            if level < depth:
                subsects = self.build_contents(section, level)
                item += subsects
            entries.append(item)
        if entries:
            contents = nodes.bullet_list('', *entries)
            if auto:
                contents['classes'].append('auto-toc')
            return contents
        else:
            return []


class PDFWriter(writers.Writer):
    def __init__(self,
                builder,
                stylesheets,
                language,
                breaklevel = 0,
                fontpath = [],
                fitmode = 'shrink',
                compressed = False,
                inline_footnotes = False):
        writers.Writer.__init__(self)
        self.builder = builder
        self.output = ''
        self.stylesheets = stylesheets
        self.__language = language
        self.breaklevel = int(breaklevel)
        self.fontpath = fontpath
        self.fitmode = fitmode
        self.compressed = compressed
        self.inline_footnotes = inline_footnotes
        self.highlightlang = builder.config.highlight_language

    supported = ('pdf')
    config_section = 'pdf writer'
    config_section_dependencies = ('writers',)

    def translate(self):
        visitor = PDFTranslator(self.document, self.builder)
        self.document.walkabout(visitor)
        sio=StringIO('')
        createpdf.RstToPdf(sphinx=True,
                 stylesheets=self.stylesheets,
                 language=self.__language,
                 breaklevel=self.breaklevel,
                 #fit_mode=self.fitmode,
                 #font_path=self.fontpath,
                 inline_footnotes=self.inline_footnotes,
                 #highlightlang=self.highlightlang,
                ).createPdf(doctree=self.document,
                    output=sio,
                    compressed=self.compressed)
        self.output=unicode(sio.getvalue(),'utf-8','ignore')

    def supports(self, format):
        """This writer supports all format-specific elements."""
        return 1


class PDFTranslator(nodes.SparseNodeVisitor):
    def __init__(self, document, builder):
        nodes.NodeVisitor.__init__(self, document)
        self.builder = builder
        self.footnotestack = []
	self.top_sectionlevel = 1
        self.footnotecounter=1
        self.curfile=None
        self.footnotedict={}
        self.this_is_the_title = 1
        self.in_title = 0
        self.elements = {
            'title': document.settings.title,
        }
        self.highlightlang = builder.config.highlight_language
        
    def visit_document(self,node):
        self.footnotestack.append('')
        
    def visit_start_of_file(self,node):
        self.footnotestack.append(node['docname'])

    def depart_start_of_file(self,node):
        self.footnotestack.pop()
        
    def visit_highlightlang(self, node):
        self.highlightlang = node['lang']
        self.highlightlinenothreshold = node['linenothreshold']
        raise nodes.SkipNode
    
    def visit_literal_block(self, node):
        lang=lang_for_block(node.astext(),node.get('lang',self.highlightlang))
        replacement = nodes.literal_block()
        replacement.children = \
            pygments_code_block_directive.code_block_directive(
                                name = None,
                                arguments = [lang],
                                options = {},
                                content = node.astext().splitlines(),
                                lineno = False,
                                content_offset = None,
                                block_text = None,
                                state = None,
                                state_machine = None,
                                )
        node.parent.replace(node,replacement)
        
    def visit_footnote(self, node):
        node['backrefs']=[ '%s_%s'%(self.footnotestack[-1],x) for x in node['backrefs']]
        node['ids']=[ '%s_%s'%(self.footnotestack[-1],x) for x in node['ids']]
        node.children[0][0]=nodes.Text(str(self.footnotecounter))
        for id in node['backrefs']:
            fnr=self.footnotedict[id]
            fnr.children[0]=nodes.Text(str(self.footnotecounter))        
        self.footnotecounter+=1

    def visit_footnote_reference(self, node):
        node['ids']=[ '%s_%s'%(self.footnotestack[-1],x) for x in node['ids']]
        node['refid']='%s_%s'%(self.footnotestack[-1],node['refid'])
        self.footnotedict[node['ids'][0]]=node

    def visit_desc_annotation(self, node):
        pass
    
    def depart_desc_annotation(self, node):
        pass

# This is copied from sphinx.highlighting
def lang_for_block(source,lang):
    if lang in ('py', 'python'):
        if source.startswith('>>>'):
            # interactive session
            return 'pycon'
        else:
            # maybe Python -- try parsing it
            if try_parse(source):
                return 'python'
            else:
                return 'text'
    elif lang in ('python3', 'py3') and source.startswith('>>>'):
        # for py3, recognize interactive sessions, but do not try parsing...
        return 'pycon3'
    elif lang == 'guess':
        try:
            #return 'python'
            return guess_lexer(source).name
        except Exception:
            return None
    else:
        return lang
    
def try_parse(src):
    # Make sure it ends in a newline
    src += '\n'

    # Replace "..." by a mark which is also a valid python expression
    # (Note, the highlighter gets the original source, this is only done
    #  to allow "..." in code and still highlight it as Python code.)
    mark = "__highlighting__ellipsis__"
    src = src.replace("...", mark)

    # lines beginning with "..." are probably placeholders for suite
    src = re.sub(r"(?m)^(\s*)" + mark + "(.)", r"\1"+ mark + r"# \2", src)

    # if we're using 2.5, use the with statement
    if sys.version_info >= (2, 5):
        src = 'from __future__ import with_statement\n' + src

    if isinstance(src, unicode):
        # Non-ASCII chars will only occur in string literals
        # and comments.  If we wanted to give them to the parser
        # correctly, we'd have to find out the correct source
        # encoding.  Since it may not even be given in a snippet,
        # just replace all non-ASCII characters.
        src = src.encode('ascii', 'replace')

    try:
        parser.suite(src)
    except SyntaxError, UnicodeEncodeError:
        return False
    else:
        return True


def setup(app):
    app.add_builder(PDFBuilder)
    # PDF options
    app.add_config_value('pdf_documents', [], None)
    app.add_config_value('pdf_stylesheets', ['sphinx'], None)
    app.add_config_value('pdf_compressed', False, None)
    app.add_config_value('pdf_font_path', [], None)
    app.add_config_value('pdf_language', '', 'en_US')
    app.add_config_value('pdf_fit_mode', '', None),
    app.add_config_value('pdf_break_level', 0, None)
    app.add_config_value('pdf_inline_footnotes', True, None)
    app.add_config_value('pdf_verbosity', 0, None)
    app.add_config_value('pdf_use_index', True, None)
    app.add_config_value('pdf_use_modindex', True, None)
    app.add_config_value('pdf_use_coverpage', True, None)
    author_texescaped = unicode(app.config.copyright)\
                               .translate(texescape.tex_escape_map)
    project_doc_texescaped = unicode(app.config.project + ' Documentation')\
                                     .translate(texescape.tex_escape_map)
    app.config.pdf_documents.append((app.config.master_doc,
                                     app.config.project,
                                     project_doc_texescaped,
                                     author_texescaped,
                                     'manual'))
