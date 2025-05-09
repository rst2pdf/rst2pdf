
{next}
------

* Changed: We now use docutil's smart quotes rather than the old, abandoned smartypants library (PR #1253)

0.103.1 (2024-12-24)
--------------------
* Changed: Updated pyproject classifiers to include Python 3.13 (PR #1258)
* Changed: Various project changes to allow releasing using uv (PR #1255, PR #1256, PR #1257)


0.103 (2024-12-24)
------------------

* Added: We now support Python 3.13 (PR #1236)
* Added: We now support ``emphasize-lines`` asa an alias for ``hl_lines`` (PR #1246)
* Changed: Support PyMuPDF when it's installed as fitz_old (PR #1225)
* Changed: We now use pyproject.toml and uv (PR #1240, PR #1242)
* Fixed: We now run our Sphinx tests again (PR #1241)
* Fixed: We no longer add a second document to Sphinx builds (PR #1243)


0.102 (2024-06-05)
------------------

* Added: We now set ``supported_image_type`` attribute in the Sphinx builder (PR #1201)
* Changed: We now support ReportLab 4 and xhtml2pdf 0.12.2 (PR #1214)
* Fixed: CI now correctly fails if the tests fail (PR #1212)


0.101 (2023-08-02)
------------------

* Changed: We now recommend using pipx to install rst2pdf. (PR #1166)
* Changed: The manual's examples for embedding fonts are now better. (PR #1156)
* Fixed: The ``twocolumn.yaml`` stylesheet has been restored after inadvertent removal in 0.100. (PR #1160)
* Fixed: We now use ``ConfigParser`` so that we are ready for 3.12. (PR #1171)
* Fixed: Tests now run correctly regardless of locale. (PR #1145)
* Fixed: Arguments when calling ``DelayedTable`` are now in the correct order. (PR #1150)


0.100 (2023-03-20)
------------------

* Added: New command line option ``--record-dependencies`` to write out the list of files that were
  used to create the PDF.(PR #1111)
* Added: Python 3.11 is now experimentally supported. Please report any issues found. (PR #1133)
* Changed: Updated tests to use ReportLab 3.6.12. Note that ReportLab 3.6.5 introduced some layout
  changes in rst2pdf's output. We have noticed that header/footer spacing is different, the space
  before nested bullets is bigger than before and that some fully-justified text paragraphs now
  wrap differently. (PR #1110)
* Fixed: The ``twoColumn`` style has been reinstated as its used with Sphinx. (PR #1126)


0.99 (2022-01-08)
-----------------

* Added: Python 3.9 & 3.10 are now supported (PR #969, #1043)
* Added: Sphinx 4 is now supported. (PR #1020)
* Added: Can now set background images using ``PageBreak``. (PR #1050)
* Added: Can now set multiple style names in the ``class`` directive (PR #1048)
* Added: ``pdf_smartquotes`` option is now supported with Sphinx builds (PR #1045)
* Added: Add support for styling separations. (PR #927)
* Changed: Outline entries that are deeper than the ToC are now collapsed (PR #1049)
* Changed: ``math`` directive updated to support latest matplotlib (PR #1047)
* Changed: the ``--very-verbose`` option provides more information when things go wrong. (PR #1025)
* Changed: The default stylesheet has been improved. Use the ``rst2pdf-0.9`` stylesheet to apply the
  previous default as per the "Migrating to the New Default Stylesheet" section of the manual. Also,
  the ``twoColumn`` style is no longer part of the default styles and is now a separate style. Add
  ``-s twocolumn`` to apply it or, for Sphinx add ``pdf_stylesheets = ['twocolumn']`` (PR #988)
* Changed: Stylesheets are now in YAML. Migrate to the new format using ``python -m rst2pdf.style2yaml``
  as per the "Migrating Stylesheet Format" section of the manual. (PR #956)
* Fixed: An imagine that is too tall in a table cell is now resized to fit. (PR #1024)
* Fixed: rst2pdf now writes to stdout again (PR #994)
* Fixed: Ensure table columns are wide enough for use (PR #992)
* Fixed: Better error messages for malformed RST (PR #990)
* Fixed: The Sphinx versionadded & versionchanged directives work again (PR #982)
* Fixed: Hyperlinks with embedded internal link aliases no longer crash. (PR #972, #979)
* Fixed: A more sensible error message is displayed when importing an extension fails (PR #954)
* Fixed: If rst2pdf errors, it should now return a non-zero status code. (PR #925, #1041, #1046)
* Fixed: Various documentation improvements (PR #913, #933, #943)
* Fixed: Addressed regular expression FutureWarning. (PR #908)
  supported. (PR #937)
* Removed: Documentation related to kerning has been removed as it depended on word-axe which is longer


0.98 (2020-08-28)
-----------------

* Added: We can now create coverage reports using ``tox -e coverage``. (Issues 890)
* Changed: Update Pygments styles (Issue #882)
* Changed: Update Pillow dependency in requirements.txt. (Issue #858)
* Changed: Use content-based comparison in tests. (Issue #854)
* Fixed: Elements with that that don't have an rst2pdf element (e.g. subtitles, inline references) no
  longer cause a crash,  (Issue #889, #899)
* Fixed: SVGlib is really optional now! (Issue #889)
* Fixed: The README, LICENSE and CHANGES files are now packaged with the release tarball. (Issue #867)
* Removed: Support for pdfrw has been removed and hence support for rendering SVGs using Inkscape has
  also been removed. (Issue #896)
* Removed: Wordaxe support has been removed (Issue #887)

0.97 (2020-05-09)
-----------------

* Update Pillow dependency in requirements.txt. (Issue #858)
* Fixed: The styles directory is now packaged with the release tarball. (Issue 857)
* Fixed: Sphinx config settings pdf_real_footnotes and pdf_use_toc are now boolean. Note
  that value of pdf_real_footnotes is not False if not explicitly set. (Issue #846)
* Changed: We have moved to pytest (Issue #850)

0.96 (2020-01-05)
-----------------

* Fixed: Manual now builds again (Issue #834)

0.95 (2019-12-30)
-----------------

* Added: Python 3 is now supported (Issues #744, #745, #780, #788, #811, #814)
* Added: The code-block's language attribute is now optional (Issue #823)
* Added: Inkscape 1.x is now supported by the inkscape extension (Issue #821)
* Added: Units can now be specified in spaceBefore/spaceAfter for stylesheets (Issue #754)
* Added: Frame padding can now be specified  in stylesheets (Issue #753)
* Changed: Migrated from svg2rlg to svglib, which is maintained and supports python 3 (Issue #745)
* Changed: We now use docutils math directive instead of rst2pdf's (Issue #722)
* Fixed: Internal links now work when using ReportLab 3.5.19+ (Issue #772)
* Removed: Support Psyco has been removed (Issue #756)
* Removed: Support for PythonMagick, GFX and SWFTools has been removed (Issue #756)

0.94.1 (2019-05-25)
-------------------

* Update urllib3 and Jinja2 dependencies in requirements.txt (Issue #775)
* Fix "reportlab is not defined" error when using ReportLab 3.5.20+ (Issue #774)

0.94 (2019-01-24)
-----------------

* Added: ``:hl_lines:`` code directive allows highlighting of specific lines (Issue #623)
* Added: ``repeat_table_rows`` is now supported in Sphinx (Issue #505)
* Added: ``scale_width`` is now supported for ``--fit-background-mode`` (Issue #505)
* Added: Extension metadata for Sphinx is now returned in pdfbuilder (Issue 640)
* Added: The Sphinx ``today`` config setting is now used if it is set
* Changed: ``:start-after:`` will now render the next line
* Changed: Updated reportlab dependency to 3.5.12 and Sphinx to 1.7.9 (Issue #718)
* Changed: We no longer logging.basicConfig configuration (Issue #509)
* Changed: We now use PILLOW rather than PIL
* Fixed bug in token replacement that broke tables in headers/footers (Issue #612)
* Fixed handling of empty documents, they now generate a single empty page (Issue #547)
* Fixed: ``:alt:`` option now works for plantuml extension
* Fixed: ``:linenos_offset:`` now works again
* Fixed: ``rst2pdf.createpdf.main`` now releases the input file handle
* Fixed: CreationDate metadata shows correct date using Sphinx (Issue #525)
* Fixed: Error when using --date-invariant with newer reportlab versions (Issue #678)
* Fixed: handling of non-http/ftp URLs (Issue #549)
* Fixed: Inline ``:math:`` works again as we now use quoted attributes for HTML ``<img>`` tags (Issue 567)
* Fixed: Made literal block shrinking work again (Issue #560)
* Fixed: Removed debugging print statement when using line blocks
* Fixed: Removed uniconverter from setup (Issue #487)
* Fixed: Renamed links now work (Issue #569)
* Fixed: Sphinx config setting pdf_invariant works properly now (Issue #718)
* Fixed: sphinx+rst2pdf now works with automodule directive Sphinx >= 1.4 (Issue #566)
* Fixed: Using ``:start-after:`` with ``linenos_offset`` now displays the correct line number
* Fixed: Using ``:start-at:`` with ``linenos_offset`` now displays the correct line number
* Removed: Our own copy of smartypants. We now use the PyPI package instead (Issue #694)
* Removed: Tenjin has been switched to Jinja2 (Issue #696)
* Removed: The QT4 GUI is no more (Issue #690)

0.93 (2012-12-18)
-----------------

* Fixed Issue 447: Double-sided always starts on the right (By Rob Ludwick)

  * Removed --first-page-even as it was not used anywhere.
  * Added --first-page-on-right

* Fixed Issue 464: support alignment via :class: in image directives.
* Fixed Issue 482: Line blocks with indented parts get extraneous spacing
* Fixed Issue 470: Support for :target: in figures.
* New style "image" to be applied to image directives.
* Fixed Issue 485: Better styling support for figures/images (spaceBefore/After)
* Support rst2pdf [inf [outf]] syntax to be more compatible with rst2*
* Implemented Issue 389: New --strip-element-with-class option
* Fixed Issue 474: CellStyle1 is not there in reportlab 2.6
* Removed default padding from DelayedTable, which looked bad
  on headers/footers.
* Improvements to the math directive (font color and size)
* Better support for styling literals.
* Fixed Issue 454 (Splitting failure)
* Regressed Issue 374 (some literal blocks get oversplit)
* Switched from svglib to svg2rlg
* Removed uniconvertor support
* Fixed Issue 477: Sink footnote separator (patch by asermax)
* Fixed Issue 473: Support "code" directive like an alias of code-block.
* Fixed Issue 472: Implemented MyImage._unRestrictSize
* Fixed Issue 471: Respect class in lineblocks.
* Fixed Issue 455: New pisa/xhtml2pdf has very different imports
* Reopened Issue 289: Broken bullet customization.
* Reopened Issue 310: Line numbers in code blocks are wrong
* Reopened Issue 337: Bad layout with inline images in tables
* Marked Issue 358 as fixed.
* Fixed Issue 410: always include full lines in code-blocks (mmueller patch)
* Regression in fancytitles extension: Issue 486


0.92 (2012-06-01)
-----------------

* Fixed Issue 394; missing _restrictSize method with RL 2.5
* Fixed Issue 452: applying missing classes to lists crashed rst2pdf
* Fixed Issue 427: multiple spaces collapsed on inline literals.
* Fixed Issue 451: roman.py was moved in docutils 0.9
* Fixed Issue 446: made it work again with python 2.4


0.91 (2012-03-06)
-----------------

* Fixed Issue 438: sphinx support was completely broken in 0.90


0.90 (2012-03-04)
-----------------

* Added raw HTML support, by Dimitri Christodoulou
* Fixed Issue 422: Having no .afm files made font lookup slow.
* Fixed Issue 411: Sometimes the windows registry has the font's abspath.
* Fixed Issue 430: Using --config option caused other options to
  be ignored (by charles at cstanhope dot com)
* Fixed Issue 436: Add pdf_style_path to sphinx (by tyler@datastax.com)
* Fixed Issue 428: page numbers logged as errors
* Added support for many pygments options in code-block (by Joaquin Sorianello)
* Implemented Issue 404: plantuml support
* Issue 399: support sphinx's template path option
* Fixed Issue 406: calls to the wrong logging function
* Implemented Issue 391: New --section-header-depth option.
* Fixed Issue 390: the --config option was ignored.
* Added support for many pygments options in code-block (by Joaquin Sorianello)
* Fixed Issue 379: Wrong style applied to paragraphs in definitions.
* Fixed Issue 378: Multiline :address: were shown collapsed.
* Implemented Issue 11: FrameBreak (and conditional FrameBreak)
* The description of frames in page templates was just wrong.
* Fixed Issue 374: in some cases, literal blocks were split inside
  a page, or the pagebreak came too early.
* Fixed Issue 370: warning about sphinx.addnodes.highlightlang not being
  handled removed.
* Fixed Issue 369: crash in hyphenator when specifying "en" as a language.
* Compatibility fix to Sphinx 0.6.x (For python 2.7 docs)


0.16 (2010-10-06)
-----------------

* Fixed Issue 343: Plugged memory leak in the RSON parser.
* Fix for Issue 287: there is still a corner case if you have two sections
  with the same title, at the same level, in the same page, in different files
  where the links will break.
* Fixed Issue 367: german-localized dates are MM. DD. YYYY so when used in sphinx's
  template cover they appeared weird, like a list item. Fixed with a minor workaround in
  the template.
* Fixed Issue 366: links to "#" make no sense on a PDF file
* Made definitions from definition lists more stylable.
* Moved definition lists to SplitTables, so you can have very long
  definitions.
* Fixed Issue 318: Implemented Domain specific indexes for Sphinx 1.0.x
* Fixed Index links when using Sphinx/pdfbuilder.
* Fixed Issue 360: Set literal.wordWrap to None by default so it doesn't inherit
  wordWrap CJK when you use the otherwise correct japanese settings. In any case,
  literal blocks are not supposed to wrap at all.
* Switched pdfbuilder to use SplitTables by default (it made no sense not to do it)
* Fixed Issue 365: some TTF fonts don't validate but they work anyway.
* Set a valid default baseurl for Sphinx (makes it much faster!)
* New feature: --use-numbered-links to show section numbers in links to sections, like  "See section 2.3 Termination"
* Added stylesheets for landscape paper sizes (i.e: a4-landscape.style)
* Fixed Issue 364: Some options not respected when passed in per-doc options
  in sphinx.
* Fixed Issue 361: multiple linebreaks in line blocks were collapsed.
* Fixed Issue 363: strange characters in some cases in math directive.
* Fixed Issue 362: Smarter auto-enclosing of equations in $...$
* Fixed Issue 358: --real--footnotes defaults to False, but help text indicates default is True
* Fixed Issue 359: Wrong --fit-background-mode help string
* Fixed Issue 356: missing cells if a cell spawns rows and columns.
* Fixed Issue 349: Work correctly with languages that are available in form  aa_bb and not aa (example: zh_cn)
* Fixed Issue 345: give file/line info when there is an error in a raw PDF directive.
* Fixed Issue 336: JPEG images should work even without PIL (but give a warning because
  sizes will probably be wrong)
* Fixed Issue 351: footnote/citation references were generated incorrectly, which
  caused problems if there was a citation with the same text as a heading.
* Fixed Issue 353: better handling of graphviz, so that it works without vectorpdf
  but gives a warning about it.
* Fixed Issue 354: make todo_node from sphinx customizable.
* Fixed bug where nested lists broke page layout if the page was small.
* Smarter --inline-links option
* New extension: fancytitles, see http://lateral.netmanagers.com.ar/weblog/posts/BB906.html
* New feature: tab-width option in code-block directive (defaults to 8).
* Fixed Issue 340: endnotes/footnotes were not styled.
* Fixed Issue 339: class names using _ were not usable.
* Fixed Issue 335: ugly crash when using images in some
  specific places (looks like a reportlab bug)
* Fixed Issue 329: make the figure alignment/class attributes
  work more like LaTeX than HTML.
* Fixed Issue 328: list item styles were being ignored.
* Fixed Issue 186: new --use-floating-images makes images with
  :align: set work like in HTML, with the next flowable flowing
  beside it.
* Fixed Issue 307: header/footer from stylesheet now supports inline
  rest markup and substitutions defined in the main document.
* New pdf_toc_depth option for Sphinx/pdfbuilder
* New pdf_use_toc option for Sphinx/pdfbuilder
* Fixed Issue 308: compatibility with reportlab from SVN
* Fixed Issue 323: errors in the config.sample made it work weird.
* Fixed Issue 322: Image substitutions didn't work in document title.
* Implemented Issue 321: underline and strikethrough available
  in stylesheet.
* Fixed Issue 317: Ugly error message when file does not exist


0.15
----

* Fixed Issue 315: crash when using an undefined class for
  a list.
* Implemented Issue 279: images can be specified as URLs.
* Fixed Issue 313: new --fit-background-mode option.
* Fixed Issue 110: new --real-footnotes option (buggy).
* Fixed Issue 176: spacers larger than a page don't crash.
* Fixed Issue 65: References to Helvetica/Times when it was not used.
* Fixed Issue 310: added option linenos_offset to code blocks.
* Fixed Issue 309: style for blockquotes was not respected.
* Custom cover page support (related to Issue 157)
* Fixed Issue 305: support wildcards in image names
  and then use the best one available.
* Implemented Issue 298: counters
* Improved widow/orphan support for literal blocks
* Fixed Issue 304: Code blocks didn't respect fontSize in class.


0.14.2 (2010-03-26)
-------------------

* Regained compatibility with reportlab 2.3
* Fixed regression in Issue 152: right-edege of boxes not aligned inside
  list items.

* Fixed Issue 301: accept padding parameters in bullet/item lists


0.14.1 (2010-03-25)
-------------------

* Make it compatible with Sphinx 0.6.3 again
* Fixed Issue 300: image-missing.jpg was not installed


0.14 (2010-03-24)
-----------------

* Fixed Issue 197: Table borders were confusing.
* Fixed Issue 297: styles from default.json leaked onto other syntax
  highlighting stylesheets.
* Fixed Issue 295: keyword replacement in headers/footers didn't work
  if ###Page### and others was inside a table.
* New feature: oddeven directive to display alternative content on
  odd/even pages (good for headers/footers!)
* Switched all stylesheets to more readable RSON format.
* Fixed Issue 294: Images were deformed when only height was specified.
* Fixed Issue 293: Accept left/center/right as alignments in stylesheets.
* Fixed Issue 292: separate style for line numbers in codeblocks
* Fixed Issue 291: support class directive for codeblocks
* Fixed Issue 104: total number of pages in header/footer works in
  all cases now.
* Fixed Issue 168: linenos and linenothreshold options in Sphinx now
  work correctly.
* Fixed regression in 0.12 (interaction between rst2pdf and sphinx math)
* Documented extensions in the manual
* Better styling of bullets/items (Issue 289)
* Fixed Issue 290: don't fail on broken images
* Better font finding in windows (patch by techtonik, Issue 282).
* Fixed Issue 166: Implemented Sphinx's hlist (horizontal lists)
* Fixed Issue 284: Implemented production lists for sphinx
* Fixed Issue 165: Definition lists not properly indented inside
  admonitions or tables.
* SVG Images work inline when using the inkscape extension.
* Fixed Issue 268: TOCs shifted to the left on RL 2.4
* Fixed Issue 281: sphinx test automation was broken
* Fixed Issue 280: wrong page templates used in sphinx


0.13 (2010-03-15)
-----------------

* New TOC code (supports dots between title and page number)
* New extension framework
* New preprocessor extension
* New vectorpdf extension
* Support for nested stylesheets
* New headerSeparator/footerSeparator stylesheet options
* Foreground image support (useful for watermarks)
* Support transparency (alpha channel) when specifying colors
* Inkscape extension for much better SVG support
* Ability to show total page count in header/footer
* New RSON format for stylesheets (JSON superset)
* Fixed Issue 267: Support :align: in figures
* Fixed Issue 174 regression (Indented lines in line blocks)
* Fixed Issue 276: Load stylesheets from strings
* Fixed Issue 275: Extra space before lineblocks
* Fixed Issue 262: Full support for Reportlab 2.4
* Fixed Issue 264: Splitting error in some documents
* Fixed Issue 261: Assert error with wordaxe
* Fixed Issue 251: added support for rst2pdf extensions when using sphinx
* Fixed Issue 256: ugly crash when using SVG images without SVG support
* Fixed Issue 257: support aafigure when using sphinx/pdfbuilder
* Initial support for graphviz extension in pdfbuilder
* Fixed Issue 249: Images distorted when specifiying width and height
* Fixed Issue 252: math directive conflicted with sphinx
* Fixed Issue 224: Tables can be left/center/right aligned in the page.
* Fixed Issue 243: Wrong spacing for second paragraphs in bullet lists.
* Big refactoring of the code.
* Support for Python 2.4
* Fully reworked test suite, continuous integration site.
* Optionally use SWFtools for PDF images
* Fixed Issue 231 (Smarter TTF autoembed)
* Fixed Issue 232 (HTML tags in title metadata)
* Fixed Issue 247 (printing stylesheet)


0.12.3
------

* Fixed Issue 230 (Admonition titles were not translated)
* Fixed Issue 228 (page labels and numbers match, so page ii is the
  same on-page and in the PDF TOC)
* Fixed Issue 227 (missing background should not be fatal error)
* Fixed Issue 225 (bad spacing in lineblocks)
* Fixed Issue 223 (non-monospaced styles used in code)


0.12.2 (2009-10-19)
-------------------

* Fix Issue 219 (incompatibility with reportlab 2.1)
* Added pdf_default_dpi option for pdfbuilder
* More style docs in the manual
* Better styling of lists
* Fix bug reported in comments in my blog where a stylesheet with
  showHeader=True and no explicit header caused an exception.
* Fixed Issue 215: crashes in bookrest's background renderer.


0.12.1 (2009-10-14)
-------------------

* Ship local patched copy of pypoppler-qt4
* Partial fix for Issue 205: KeyError: 'format'
* Fixed Issue 212: XML parsing error in bookrest
* Fixed Issue 210: pickle error in bookrest
* Switched --enable-splittables to True by default
* Fixed Issue 204: syntax error on font importing code


0.12 (2009-10-10)
-----------------

* Fixed Issue 202: broken processing of HTML raw nodes
* New "options" section in stylesheets. New ["options"]["stylesheets"] subsection,
  which works similar to -s or to an include file: a list of stylesheets to be
  processed before the current one.
* New --config option
* Fix for Issue 200 (position of frames was miscalculated)
* Fix For Issue 188 (uniconvertor "'unicode' object has no attribute 'readline'" error)
* New raw directive command: SetPageCounter. This enables
  page counter manipulation, and use of different styles,
  roman, lowerroman, alpha, loweralpha and arabic.
* New raw directive commands: EvenPageBreak and OddPageBreak
* New option to make sections break to odd or even pages:
  --break-side=VALUE
* New option to add an empty page at the beginning of the
  document: --blank-first-page.
* Fixed bug in authors field width calculation
* Support % in bullet and field lists column widths
* Use bullet_list or item_list styles for bullet and item lists respectively.
* Support % in field list column width description.
* Fix for Issue 184 (font metrics go crazy with TT font)
* New admonition code based on SplitTable (beta quality)
* Fix for Issue 180 (support for very very long list items. Needs testing)
* Fix for Issue 175 (widow/orphan titles)
* Fix for Issue 174 (line blocks didn't respect indentation)
* Worked around Issue 173 (quotes didn't indent inside table cells)
* Respect spaceBefore and spaceAfter for footnotes/endnotes
* Added tests for (almost) all of sphinx's custom markup
* Fixed Issue 170 (Wrong font embedding)
* Fixed Issue 171 (Damaged xref table)
* Fixed Issue 159 (Admonition and table widths were miscalculated)
* Fixed Issue 162 (wrong highlighting using sphinx)
* Changed default language policy as described in Issue 53
* Fixed Issue 148 (Images should be looked for relative to source document)
* Fixed Issue 158 (Some admonitions crashed pdfbuilder)
* Fixed Issue 154 (incompatibility with RL 2.1)
* Fixed Issue 155 (crash when sidebars split in a certain way)
* Fixed issue 152 (padding and alignment of table styles, like
  when using literal blocks inside lists)
* Integrated pdfbuilder sphinx extension (more work needed)
* Kerning support for true type fonts (thanks to wordaxe!), added
  to the docs, added convenience stylesheet.
* Fixed Issue 151 and behaviour on Issue 116, about images too large
  for available space / the full frame height.
* Fixed problem in admonition titles.
* Fixed section names in headers/footers: FIRST section on the page
  is used, not LAST.
* Fixed Issue 145: padding of literal blocks was broken.
* Fixed bug: paragraphs with ids should have the matching anchors
* Fixed bug: internal references were not linked correctly
* Fixed Issue 144: PDF TOC had wrong page numbers in some cases
* More sphinx compatibility
* New table styles code, also make class directive work for tables
* Fixed Issue 140: html-like markup in titles was kept in the PDF TOC
* Fixed Issue 138: Redid figure styling. Also fixed bugs in BoxedContainer
* Fixed Issue 137: bugs in escaping characters in interpreted roles
* Make it work (in a slightly degraded mode) without PIL, as
  long as you are only using JPGs or have PythonMagick installed.
  This is good for OS X, where "installing PIL is a PITA"
* Fixed issue 134: entities were replaced in interpreted roles
  (not needed)
* Support for aafigure (http://launchpad.net/aafigure)
* Spacers support units
* TOC styles now configurable in stylesheet


0.11 (2009-06-20)
-----------------

* Degrade more gracefully when one or more wordaxe hyphenators are
  broken (currently DWC is the broken one)
* Fixed issue 132: in some cases, with user-defined fontAlias, bold and
  italic would get confused (getting italic instead of bold in inline
  markup, for instance).
* New stylesheet no-compact-lists to make lists... less compact
* SVG images now handle % as a width unit correctly.
* Implemented issue 127: support images in PDF format. Right now they
  are rasterized, so it's not ideal. Perhaps something better will come up
  later.
* Fixed issue 129: make it work around a prblem with KeepTogether in RL 2.1
  it probably makes the output look worse in some cases when using that.
  RL 2.1 is not really supported, so added a warning.
* Fixed issue 130: use os.pathsep instead of ":" since ":" in windows is used
  in disk names (and we still pay for DOS idiocy, in 2009)
* Fixed issue 128: headings level 3+ all looked the same
* Ugly bugfix for Issue 126: crashes when using images in header + TOC
* New tstyles section in the stylesheet provides more configurable list layouts
  and more powerful table styling.
* Better syntax highlighting (supports bold/italic)
* Workaround for issue 103 so you can use borderPadding as a list (but it will look wrong
  if you are using wordaxe <= 0.3.2)
* Added fieldvalue style for field lists
* Added optionlist tstyle, for option lists
* Added collection of utility stylesheets and documented it
* Improved command line parsing and stylesheet loading (guess
  extension like latest rst2latex does)
* Fixed Issue 67: completely new list layouting code
* Fixed Issue 116: crashes caused by huge images
* Better support for %width in images, n2ow it's % of the container frame's
  width, not of the text area.
* Fixed bug in SVG scaling
* Better handling of missing images
* Added missing styles abstract, contents, dedication to the default stylesheet
* Tables style support spaceBefore and spaceAfter
* New topic-title style for topic titles (obvious ;-)
* Vertical alignment for inline images (:align: parameter)
* Issue 118: Support for :scale: in images and handle resizing of inline images
* Issue 119: Fix placement of headers and footers
* New background property for page templates (nice for presentations, for example)
* Default to px for image width specifications instead of pt
* Support all required measurement units ("em" "ex" "px" "in" "cm"
  "mm" "pt" "pc" "%" "")
* New automated scripts to check test cases for "visual differences"
* Respect images DPI property a bit like rst2latex does.
* Issue 110: New --inline-footnotes option
* Tested with reportlab from SVN trunk
* Support for Dinu Gherman's svglib. If both svglib and uniconvertor are available,
  svglib is preferred (for SVG, of course). Patch originally by rute.
* Issue 109: Separate styles for each kind of admonition
* For Issue 109: missing styles are not a fatal error
* Issue 117: TOCs with more than 6 levels now supported (raised limit to 9, which
  is silly deep)


0.10.1 (2009-05-16)
-------------------

* Issue 114: Fixed bug in PDF TOC for sections containing ampersands


0.10 (2009-05-15)
-----------------

* Issue 87: Table headers can be repeated in each page (thanks to Yasushi Masuda)
* Issue 93: Line number support for code blocks (:linenos: true)
* Issue 111: Added --no-footnote-backlinks option
* Issue 107: Support localized directives/roles (example: sommaire instead of contents)
* Issue 112: Fixed crash when processing empty list items
* Issue 98: Nobreak support, and set as default for inline-literals so they don't hyphenate.
* Slightly better tests
* Background colors in text styles work with reportlab 2.3
* Issue 99: Fixed hyphenation in headers/footers (requires wordaxe 0.3.2)
* Issue 106: Crash on demo.txt fixed (requires wordxe 0.3.2)
* Issue 102: Implemented styles for bulleted and numbered lists
* Issue 38: Default headers/footers via options, config file or stylesheet
* Issue 88: Implemented much better book-style TOCs
* Issue 100: Fixed bug with headers/footers and Reportlab 2.3
* Issue 95: Fixed bug with indented tables
* Issue 89: Implemented --version
* Issue 84: Fixed bug with relative include paths
* Issue 85: Fixed bug with table cell styles
* Issue 83: Fixed bug with numeric colors in backColor attribute
* Issue 44: Support for stdin and stdout
* Issue 79: Added --stylesheet-path option
* Issue 80: Send warnings to stderr, not stdout
* Issue 66: Implemented "smart quotes"
* Issue 77: Work around missing matplotlib
* Proper translation of labels (such as "Author", "Version" etc.) using the
  docutils languages package. (r473)
* Fixed problems with wrong or non-existing fonts. (r484)
* Page transition effect support for presentations (r423)



0.9 (2008-09-26)
----------------

* Math support via Mathplotlib
* Huge bug in header/footer page numbers/section names fixed
* Several bugs in nested lists fixed (not 100% correct yet, but better)
* Lists that don't start at 1 work now
* Nicer definition lists


0.8.1 (2008-09-19)
------------------

* Support for more complex headers and footers
  (including image directives and tables)
* Optional inline links
* Wordaxe 0.2.6 support
* Several bugs fixed (issues 48,68,41,60,58,64,67)
* Support for system-wide config file
* Better author metadata


0.8 (2008-09-12)
----------------

* Support for vector graphics: SVG, EPS, PS, CDR and others (requires uniconvertor)
* Support for stdin and stdout, so you can use rst2pdf in pipes.
* Works with reportlab 2.1 and 2.2
* Simpler stylesheets (guess bulletFontName, leading, bulletFontSize from other parameters)
* Some support for sphinx
* Fixed the docutils Writer interface
* Continue processing when an image is missing
* Support for user config file
* Font sizes can be expressed in units or % of parent style's size
* Larger font size in the default stylesheet


0.7 (2008-09-05)
----------------

* Automatic Type1 and True Type font embedding. Just use the font or family name, and (with a little luck), it will be embedded for you.
* width attribute in styles, to create narrow paragraphs/tables
* Styles for table headers and table cells
* "Zebra tables"
* Improvements in the handling of overflowing literal blocks (code, for instance)
* Different modes to handle too-large literal blocks: overflow/truncate/shrink.
* Real sidebars and "floating" elements.
* Fixed link style (no ugly black underlining!)


0.6 (2008-08-30)
----------------

* Stylesheet-defined page layout (For example, multicolumn) and layout switching
* Cascading Stylesheets (change exactly what you need changed)
* PDF table of contents
* Current section names and numbers in headers/footers
* Support for compressed PDF files
* Link color is configurable
* Fixed bugs in color handling
* Multilingual hyphenation
* Auto-guessing image size, support for sizes in %
* Gutter margins
* Big refactoring
* More tolerant of minor problems
* Limited _raw_ directive (you can insert pagebreaks and vertical space)
* Implemented a "traditional" docutils writer
* Offer a reasonable API for use as a library
* Fixed copyright/licensing
* code-block now supports including files (whole or in part) so you can highlight external code.



0.5 (2008-08-27)
----------------

* Support for :widths: in tables
* Support for captions in tables
* Support for multi-row headers in tables
* Improved definition lists
* Fixed bug in image directive
* Whitespace conforming to PEP8
* Fixed bug in text size on code-block
* Package is more setuptools compliant
* Fix for option groups in option lists
* Citations support
* Title reference role fix


0.4 (2008-08-25)
----------------

* Fixed bullet and item lists indentation/nesting.
* Implemented citations
* Working links between footnotes and its references
* Justification enabled by default
* Fixed table bug (demo.txt works now)
* Title and author support in PDF properties
* Support for document title in header/footer
* Custom page sizes and margins


0.3 (2008-08-25)
----------------

* Font embedding (use any True Type font in your PDFs)
* Syntax highlighter using Pygments
* User's manual
* External/custom stylesheets
* Support for page numbers in header/footer
