# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms
#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

__docformat__ = 'reStructuredText'

from reportlab.platypus import *
from reportlab.platypus.doctemplate import *
from reportlab.lib.enums import *
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import *
from reportlab.platypus.flowables import _listWrapOn, _FUZZ
from reportlab.platypus.tableofcontents import TableOfContents

import styles
from log import log

import functools


class MyImage(Image):
    """A Image subclass that can take a 'percentage_of_container' kind,
    which resizes it on wrap() to use... well, a percentage of the
    container's width.

    This whole class is a huge ungainly hack that deserves flaming death.
    However, I have asked in the reportlab list for this feature. If they
    implement it ... hey, I kill this in a jiffie.

    """

    def __init__(self, filename, width=None, height=None,
                 kind='direct', mask="auto", lazy=1):
        self.__kind=kind
        if kind == 'percentage_of_container':
            Image.__init__(self, filename, width, height,
                'direct', mask, lazy)
            self.drawWidth=width
            self.drawHeight=height
            self.__width=width
            self.__height=height
        else:
            Image.__init__(self, filename, width, height,
                kind, mask, lazy)
        self.__ratio=float(self.imageWidth)/self.imageHeight
        self.__wrappedonce=False

    def wrap(self, availWidth, availHeight):
        if self.__kind=='percentage_of_container':
            w, h= self.__width, self.__height
            if not w:
                log.warning('Scaling image as % of container with w unset.'
                'This should not happen, setting to 100')
                w = 100
            scale=w/100.
            w = availWidth*scale
            h = w/self.__ratio
            self.drawWidth, self.drawHeight = w, h
            return w, h
        else:
            if self.drawHeight > availHeight:
                if not self.__wrappedonce:
                    self.__wrappedonce = True
                    return Image.wrap(self, availWidth, availHeight)
                else: # Adjust by height
                    # FIXME get rst file info (line number)
                    # here for better error message
                    log.warning('image %s is too tall for the '\
                                'frame, rescaling'%\
                                self.filename)
                    self.drawHeight = availHeight
                    self.drawWidth = availHeight*self.__ratio
            elif self.drawWidth > availWidth:
                log.warning('image %s is too wide for the frame, rescaling'%\
                            self.filename)
                self.drawWidth = availWidth
                self.drawHeight = availWidth / self.__ratio
            return Image.wrap(self, availWidth, availHeight)


class MyIndenter(Indenter):
    """I can't remember why this exists."""

    width = 0
    height = 0

    def draw(self):
        pass


class OutlineEntry(Flowable):
    """Creates outline entries in the PDF TOC."""

    def __init__(self, label, text, level=0, snum=None):
        """Initialize outline entries.

            * label is a unique label.
            * text is the text to be displayed in the outline tree
            * level is the level, 0 is outermost, 1 is child of 0, etc.

        """
        if label is None: # it happens
            self.label = text.replace(u'\xa0', ' ').strip(
                ).replace(' ', '_').encode('ascii', 'replace')
        else:
            self.label = label.strip()
        self.text = text.strip()
        self.level = int(level)
        self.snum = snum
        Flowable.__init__(self)

    def wrap(self, w, h):
        """This takes no space"""
        return 0, 0

    def draw(self):
        self.canv.bookmarkPage(self.label)
        self.canv.sectName = self.text
        if self.snum is not None:
            self.canv.sectNum = self.snum
        else:
            self.canv.sectNum = ""
        self.canv.addOutlineEntry(self.text, self.label, self.level, False)

    def __repr__(self):
        return "OutlineEntry (label=%s , text=%s , level=%d) \n" % (
            self.label, self.text, self.level)


class Separation(Flowable):
    """A simple <hr>-like flowable"""

    def wrap(self, w, h):
        self.w = w
        return w, 1*cm

    def draw(self):
        self.canv.line(0, 0.5*cm, self.w, 0.5*cm)


class Reference(Flowable):
    """A flowable to insert an anchor without taking space"""

    def __init__(self, refid):
        self.refid = refid
        Flowable.__init__(self)

    def wrap(self, w, h):
        """This takes no space"""
        return 0, 0

    def draw(self):
        self.canv.bookmarkPage(self.refid)

    def repr(self):
        return "Anchor: %s" % self.refid


class DelayedTable(Flowable):
    """A flowable that inserts a table for which it has the data.

    Needed so column widths can be determined after we know on what frame
    the table will be inserted, thus making the overal table width correct.

    """

    def __init__(self, data, colwidths, style, repeatrows=False):
        self.data = data
        self.colwidths = colwidths
        self.style = style
        self.t = None
        self.repeatrows = repeatrows

    def wrap(self, w, h):
        # Create the table, with the widths from colwidths reinterpreted
        # if needed as percentages of frame/cell/whatever width w is.

        #_tw = w/sum(self.colwidths)
        adjust=functools.partial(styles.adjustUnits, total=w)
        colwidths=map(adjust, self.colwidths)
        #colwidths = [_w * _tw for _w in self.colwidths]
        self.t = Table(self.data, colWidths=colwidths,
            style=self.style, repeatRows=self.repeatrows)
        return self.t.wrap(w, h)

    def split(self, w, h):
        return self.t.split(w, h)

    def drawOn(self, canvas, x, y, _sW=0):
        self.t.drawOn(canvas, x, y, _sW)


class MyPageBreak(FrameActionFlowable):

    def __init__(self, templateName=None):
        self.templateName = templateName

    def frameAction(self, frame):
        frame._generated_content = [SetNextTemplate(self.templateName)]
        if not frame._atTop:
            frame._generated_content.append(PageBreak())


class SetNextTemplate(Flowable):
    """Set canv.templateName when drawing.

    rst2pdf uses that to switch page templates.

    """

    def __init__(self, templateName=None):
        self.templateName = templateName
        Flowable.__init__(self)

    def draw(self):
        if self.templateName:
            self.canv.templateName = self.templateName


class Transition(Flowable):
    """Wrap canvas.setPageTransition.

    Sets the transition effect from the current page to the next.

    """

    PageTransitionEffects = dict(
        Split=['direction', 'motion'],
        Blinds=['dimension'],
        Box=['motion'],
        Wipe=['direction'],
        Dissolve=[],
        Glitter=['direction'])

    def __init__(self, *args):
        if len(args) < 1:
            args = [None, 1] # No transition
        # See if we got a valid transition effect name
        if args[0] not in self.PageTransitionEffects:
            log.error('Unknown transition effect name: %s' % args[0])
            args[0] = None
        elif len(args) == 1:
            args.append(1)

        # FIXME: validate more
        self.args = args

    def wrap(self, aw, ah):
        return 0, 0

    def draw(self):
        kwargs = dict(
            effectname=None,
            duration=1,
            direction=0,
            dimension='H',
            motion='I')
        ceff = ['effectname', 'duration'] +\
            self.PageTransitionEffects[self.args[0]]
        for argname, argvalue in zip(ceff, self.args):
            kwargs[argname] = argvalue
        kwargs['duration'] = int(kwargs['duration'])
        kwargs['direction'] = int(kwargs['direction'])
        self.canv.setPageTransition(**kwargs)


class SmartFrame(Frame):
    """A (Hopefully) smarter frame object.

    This frame object knows how to handle a two-pass
    layout procedure (someday).

    """

    def __init__(self, container, x1, y1, width, height,
            leftPadding=6, bottomPadding=6, rightPadding=6, topPadding=6,
            id=None, showBoundary=0, overlapAttachedSpace=None, _debug=None):
        self.container = container
        self.onSidebar = False
        Frame.__init__(self, x1, y1, width, height,
            leftPadding, bottomPadding, rightPadding, topPadding,
            id, showBoundary, overlapAttachedSpace, _debug)


class FrameCutter(FrameActionFlowable):

    def __init__(self, dx, width, flowable, padding, lpad, floatLeft=True):
        self.width = width
        self.dx = dx
        self.f = flowable
        self.padding = padding
        self.lpad = lpad
        self.floatLeft = floatLeft

    def frameAction(self, frame):
        idx = frame.container.frames.index(frame)
        if self.floatLeft:
            # Don´ t bother inserting a silly thin frame
            if self.width-self.padding > 30:
                f1 = SmartFrame(frame.container,
                    frame._x1 + self.dx - 2*self.padding,
                    frame._y2 - self.f.height - 3*self.padding,
                    self.width + 2*self.padding,
                    self.f.height + 3*self.padding,
                    bottomPadding=0, topPadding=0, leftPadding=self.lpad)
                f1._atTop = frame._atTop
                # This is a frame next to a sidebar.
                f1.onSidebar = True
                frame.container.frames.insert(idx + 1, f1)
            # Don't add silly thin frame
            if frame._height-self.f.height - 2*self.padding > 30:
                frame.container.frames.insert(idx + 2,
                    SmartFrame(frame.container,
                        frame._x1,
                        frame._y1p,
                        self.width + self.dx,
                        frame._height - self.f.height - 3*self.padding,
                        topPadding=0))
        else:
            # Don´ t bother inserting a silly thin frame
            if self.width-self.padding > 30:
                f1 = SmartFrame(frame.container,
                    frame._x1 - self.width,
                    frame._y2 - self.f.height - 2*self.padding,
                    self.width,
                    self.f.height + 2*self.padding,
                    bottomPadding=0, topPadding=0, rightPadding=self.lpad)
                f1._atTop = frame._atTop
                # This is a frame next to a sidebar.
                f1.onSidebar = True
                frame.container.frames.insert(idx + 1, f1)
            if frame._height - self.f.height - 2*self.padding > 30:
                frame.container.frames.insert(idx + 2,
                    SmartFrame(frame.container,
                        frame._x1 - self.width,
                        frame._y1p,
                        self.width + self.dx,
                        frame._height - self.f.height - 2*self.padding,
                        topPadding=0))


class Sidebar(FrameActionFlowable):

    def __init__(self, flowables, style):
        self.style = style
        self.width = self.style.width
        self.flowables = flowables

    def frameAction(self, frame):
        if self.style.float not in ('left', 'right'):
            return
        if frame.onSidebar: # We are still on the frame next to a sidebar!
            frame._generated_content = [FrameBreak(), self]
        else:
            w = frame.container.styles.adjustUnits(self.width, frame.width)
            idx = frame.container.frames.index(frame)
            padding = self.style.borderPadding
            width = self.style.width
            self.style.padding = frame.container.styles.adjustUnits(
                str(padding), frame.width)
            self.style.width = frame.container.styles.adjustUnits(
                str(width), frame.width)
            self.kif = BoxedContainer(self.flowables, self.style)
            if self.style.float == 'left':
                self.style.lpad = frame.leftPadding
                f1 = SmartFrame(frame.container,
                    frame._x1,
                    frame._y1p,
                    w - 2*self.style.padding,
                    frame._y - frame._y1p,
                    leftPadding=self.style.lpad, rightPadding=0,
                    bottomPadding=0, topPadding=0)
                f1._atTop = frame._atTop
                frame.container.frames.insert(idx+1, f1)
                frame._generated_content = [
                    FrameBreak(),
                    self.kif,
                    FrameCutter(w,
                        frame.width - w,
                        self.kif,
                        padding,
                        self.style.lpad,
                        True),
                    FrameBreak()]
            elif self.style.float == 'right':
                self.style.lpad = frame.rightPadding
                frame.container.frames.insert(idx + 1,
                    SmartFrame(frame.container,
                        frame._x1 + frame.width - self.style.width,
                        frame._y1p,
                        w, frame._y-frame._y1p,
                        rightPadding=self.style.lpad, leftPadding=0,
                        bottomPadding=0, topPadding=0))
                frame._generated_content = [
                    FrameBreak(),
                    self.kif,
                    FrameCutter(w,
                        frame.width - w,
                        self.kif,
                        padding,
                        self.style.lpad,
                        False),
                    FrameBreak()]


class BoundByWidth(Flowable):
    """Limit a list of flowables by width.

    This still lets the flowables break over pages and frames.

    """

    def __init__(self, maxWidth, content=[], style=None, mode=None):
        self.maxWidth = maxWidth
        self.content = content
        self.style = style
        self.mode = mode
        if self.style:
            bp = self.style.__dict__.get("borderPadding", 0)
            bw = self.style.__dict__.get("borderWidth", 0)
            if isinstance(bp,list):
                self.pad = [bp[0] + bw + .1,
                            bp[1] + bw + .1,
                            bp[2] + bw + .1,
                            bp[3] + bw + .1]
            else:
                self.pad = [bp + bw + .1,
                            bp + bw + .1,
                            bp + bw + .1,
                            bp + bw + .1]
        else:
            self.pad = [0,0,0,0]
        Flowable.__init__(self)

    def identity(self, maxLen=None):
        return "<%s at %s%s%s>" % (self.__class__.__name__,
            hex(id(self)), self._frameName(),
            getattr(self, 'name', '')
                and (' name="%s"' % getattr(self, 'name', '')) or '')

    def wrap(self, availWidth, availHeight):
        """If we need more width than we have, complain, keep a scale"""
        if self.style:
            bp = self.style.__dict__.get("borderPadding", 0)
            bw = self.style.__dict__.get("borderWidth", 0)
            if isinstance(bp,list):
                self.pad = [bp[0] + bw + .1,
                            bp[1] + bw + .1,
                            bp[2] + bw + .1,
                            bp[3] + bw + .1]
            else:
                self.pad = [bp + bw + .1,
                            bp + bw + .1,
                            bp + bw + .1,
                            bp + bw + .1]
        else:
            self.pad = [0,0,0,0]
        maxWidth = float(min(
            styles.adjustUnits(self.maxWidth, availWidth) or availWidth,
                               availWidth))
        self.maxWidth = maxWidth
        maxWidth -= (self.pad[1]+self.pad[3])
        self.width, self.height = _listWrapOn(self.content, maxWidth, None)
        self.scale = 1.0
        if self.width > maxWidth:
            log.warning("BoundByWidth too wide to fit in frame (%s > %s): %s",
                self.width,maxWidth,self.identity())
            if self.mode == 'shrink':
                self.scale = (maxWidth + self.pad[1]+self.pad[3])/\
                    (self.width + self.pad[1]+self.pad[3])
                self.height *= self.scale
        return self.width, self.height + (self.pad[0]+self.pad[2])*self.scale

    def split(self, availWidth, availHeight):
        content = self.content
        if len(self.content) == 1:
            # We need to split the only element we have
            content = content[0].split(
                availWidth - (self.pad[1]+self.pad[3]),
                availHeight - (self.pad[0]+self.pad[2]))
            # Try splitting in our individual elements
        return [BoundByWidth(self.maxWidth, [f],
                             self.style, self.mode) for f in content]

    def draw(self):
        """we simulate being added to a frame"""
        canv = self.canv
        canv.saveState()
        x = canv._x
        y = canv._y
        _sW = 0
        scale = self.scale
        content = None
        aW = None
        #, canv, x, y, _sW=0, scale=1.0, content=None, aW=None):
        pS = 0
        if aW is None:
            aW = self.width
        aW = scale*(aW + _sW)
        if content is None:
            content = self.content
        y += (self.height + self.pad[2])/scale
        x += self.pad[3]
        for c in content:
            w, h = c.wrapOn(canv, aW, 0xfffffff)
            if (w < _FUZZ or h < _FUZZ) and not getattr(c, '_ZEROSIZE', None):
                continue
            if c is not content[0]:
                h += max(c.getSpaceBefore() - pS, 0)
            y -= h
            canv.saveState()
            if self.mode == 'shrink':
                canv.scale(scale, scale)
            elif self.mode == 'truncate':
                p = canv.beginPath()
                p.rect(x-self.pad[3],
                       y-self.pad[2],
                       self.maxWidth,
                       self.height + self.pad[0]+self.pad[2])
                canv.clipPath(p, stroke=0)
            c.drawOn(canv, x, y, _sW=aW - w)
            canv.restoreState()
            if c is not content[-1]:
                pS = c.getSpaceAfter()
                y -= pS
        canv.restoreState()


class BoxedContainer(BoundByWidth):

    def __init__(self, content, style, mode='shrink'):
        try:
            w=style.width
        except AttributeError:
            w='100%'
        BoundByWidth.__init__(self, w, content, mode=mode, style=None)
        self.style = style
        self.mode = mode

    def identity(self, maxLen=None):
        return unicode([u"BoxedContainer containing: ",
            [c.identity() for c in self.content]])

    def draw(self):
        canv = self.canv
        canv.saveState()
        x = canv._x
        y = canv._y
        _sW = 0
        lw = 0
        if self.style and self.style.borderWidth > 0:
            lw = self.style.borderWidth
            canv.setLineWidth(self.style.borderWidth)
            if self.style.borderColor: # This could be None :-(
                canv.setStrokeColor(self.style.borderColor)
                stroke=1
            else:
                stroke=0
        else:
            stroke=0
        if self.style and self.style.backColor:
            canv.setFillColor(self.style.backColor)
            fill=1
        else:
            fill=0
        if self.style:
            self.padding = self.style.__dict__.get('padding', 8)
        else:
            self.padding = 0
        self.padding += lw
        p = canv.beginPath()
        p.rect(x, y, self.width + 2*self.padding, self.height + 2*self.padding)
        canv.drawPath(p, stroke=stroke, fill=fill)
        canv.restoreState()
        BoundByWidth.draw(self)

    def split(self, availWidth, availHeight):
        self.wrap(availWidth, availHeight)
        padding = (self.pad[1]+self.pad[3])*self.scale
        if self.height + padding <= availHeight:
            return [self]
        else:
            # Try to figure out how many elements
            # we can put in the available space
            candidate = None
            remainder = None
            for p in range(1, len(self.content)):
                b = BoxedContainer(self.content[:p], self.style, self.mode)
                w, h = b.wrap(availWidth, availHeight)
                if h < availHeight:
                    candidate = b
                    if self.content[p:]:
                        remainder = BoxedContainer(self.content[p:],
                                                   self.style,
                                                   self.mode)
                else:
                    break
            if not candidate: # Nothing fits, break page
                return [FrameBreak(), self]
            if not remainder: # Everything fits?
                return [self]
            return [candidate, remainder]


if reportlab.Version == '2.1':
    import reportlab.platypus.paragraph as pla_para

    ################Ugly stuff below
    def _do_post_text(i, t_off, tx):
        """From reportlab's paragraph.py, patched to avoid underlined links"""
        xs = tx.XtraState
        leading = xs.style.leading
        ff = 0.125*xs.f.fontSize
        y0 = xs.cur_y - i*leading
        y = y0 - ff
        ulc = None
        for x1, x2, c in xs.underlines:
            if c != ulc:
                tx._canvas.setStrokeColor(c)
                ulc = c
            tx._canvas.line(t_off + x1, y, t_off + x2, y)
        xs.underlines = []
        xs.underline = 0
        xs.underlineColor = None

        ys = y0 + 2*ff
        ulc = None
        for x1, x2, c in xs.strikes:
            if c != ulc:
                tx._canvas.setStrokeColor(c)
                ulc = c
            tx._canvas.line(t_off + x1, ys, t_off + x2, ys)
        xs.strikes = []
        xs.strike = 0
        xs.strikeColor = None

        yl = y + leading
        for x1, x2, link in xs.links:
            # This is the bad line
            # tx._canvas.line(t_off+x1, y, t_off+x2, y)
            _doLink(tx, link, (t_off + x1, y, t_off + x2, yl))
        xs.links = []
        xs.link = None

    # Look behind you! A three-headed monkey!
    pla_para._do_post_text.func_code = _do_post_text.func_code
    ############### End of the ugly

class MyTableOfContents(TableOfContents):
    """
    Subclass of reportlab.platypus.tableofcontents.TableOfContents
    which supports hyperlinks to corresponding sections.
    """

    def __init__(self, *args, **kwargs):
        TableOfContents.__init__(self, *args, **kwargs)
        # reference ids for which this TOC should be notified
        self.refids = []
        # revese lookup table from (level, text) to refid
        self.refid_lut = {}
        self.linkColor = "#0000ff"

    def notify(self, kind, stuff):
        # stuff includes (level, text, pagenum, label)
        level, text, pageNum, label = stuff
        if label in self.refids:
            self.addEntry(level, text, pageNum)
            self.refid_lut[(level, text)] = label
        else:
            pass

    def wrap(self, availWidth, availHeight):
        """Adds hyperlink to toc entry."""

        widths = (availWidth - self.rightColumnWidth,
                  self.rightColumnWidth)

        # makes an internal table which does all the work.
        # we draw the LAST RUN's entries!  If there are
        # none, we make some dummy data to keep the table
        # from complaining
        if len(self._lastEntries) == 0:
            if reportlab.Version <= '2.3':
                _tempEntries = [(0, 'Placeholder for table of contents', 0)]
            else:
                _tempEntries = [(0, 'Placeholder for table of contents',
                                 0, None)]
        else:
            _tempEntries = self._lastEntries

        if _tempEntries:
            base_level = _tempEntries[0][0]
        else:
            base_level = 0
        tableData = []
        for entry in _tempEntries:
            level, text, pageNum = entry[:3]
            left_col_level = level - base_level
            if reportlab.Version > '2.3': # For ReportLab post-2.3
                leftColStyle=self.getLevelStyle(left_col_level)
            else: # For ReportLab <= 2.3
                leftColStyle = self.levelStyles[left_col_level]
            label = self.refid_lut.get((level, text), None)
            if label:
                pre = '<a href="%s" color="%s">' % (label, self.linkColor)
                post = '</a>'
                text = pre + text + post
            #right col style is right aligned
            rightColStyle = ParagraphStyle(name='leftColLevel%d' % left_col_level,
                parent=leftColStyle, leftIndent=0, alignment=TA_RIGHT)
            leftPara = Paragraph(text, leftColStyle)
            rightPara = Paragraph(str(pageNum), rightColStyle)
            tableData.append([leftPara, rightPara])

        self._table = Table(tableData, colWidths=widths, style=self.tableStyle)

        self.width, self.height = self._table.wrapOn(self.canv, availWidth, availHeight)
        return self.width, self.height
