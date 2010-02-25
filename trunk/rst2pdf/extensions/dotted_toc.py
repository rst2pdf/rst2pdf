# -*- coding: utf-8 -*-

# See LICENSE.txt for licensing terms
#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

# Some fragments of code are copied from Reportlab under this license:
#
#####################################################################################
#
#       Copyright (c) 2000-2008, ReportLab Inc.
#       All rights reserved.
#
#       Redistribution and use in source and binary forms, with or without modification,
#       are permitted provided that the following conditions are met:
#
#               *       Redistributions of source code must retain the above copyright notice,
#                       this list of conditions and the following disclaimer.
#               *       Redistributions in binary form must reproduce the above copyright notice,
#                       this list of conditions and the following disclaimer in the documentation
#                       and/or other materials provided with the distribution.
#               *       Neither the name of the company nor the names of its contributors may be
#                       used to endorse or promote products derived from this software without
#                       specific prior written permission.
#
#       THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#       ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#       WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
#       IN NO EVENT SHALL THE OFFICERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
#       INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
#       TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
#       OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
#       IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#       IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#       SUCH DAMAGE.
#
#####################################################################################

from reportlab.platypus.tableofcontents import drawPageNumbers
import rst2pdf.genelements as genelements

Table = genelements.Table
Paragraph = genelements.Paragraph

'''

NOTE:  THIS IS A HUGE HACK HACK HACK

All I did was take the wrap() method from the stock reportlab TOC generator,
and make the minimal changes to make it work on MY documents in rst2pdf.

History:

    The reportlab TOC generator adds nice dots between the text and the page number.
    The rst2pdf one does not.

    A closer examination reveals that the rst2pdf one probably deliberately stripped
    this code, because the reportlab implementation only allowed a single TOC, and
    this is unacceptable for at least some rst2pdf users.

    There are other differences in the rst2pdf one I don't understand.  This module
    is a hack to add back dots between the lines.  I think it will only work for
    RL 2.4, and will not work for multiple TOCs, so I am putting it in an extension
    module for now.  Maybe at some point we can figure out how to support dots
    with multiple TOCs in the main code.

    Mind you, the original RL implementation is a complete hack in any case:

       - It uses a callback to a nested function which doesn't even bother to
         assume the original enclosing scope is available at callback time.
         This leads it to do crazy things like eval()

       - It uses a single name in the canvas for the callback function
         (this is what kills multiple TOC capability) when it would be
         extremely easy to generate a unique name.
'''

class DottedTableOfContents(genelements.MyTableOfContents):
    def wrap(self, availWidth, availHeight):
        "All table properties should be known by now."

        # makes an internal table which does all the work.
        # we draw the LAST RUN's entries!  If there are
        # none, we make some dummy data to keep the table
        # from complaining
        if len(self._lastEntries) == 0:
            _tempEntries = [(0,'Placeholder for table of contents',0,None)]
        else:
            _tempEntries = self._lastEntries

        def drawTOCEntryEnd(canvas, kind, label):
            '''Callback to draw dots and page numbers after each entry.'''
            label = label.split(',')
            page, level, key = int(label[0]), int(label[1]), eval(label[2],{})
            style = self.getLevelStyle(level)
            if self.dotsMinLevel >= 0 and level >= self.dotsMinLevel:
                dot = ' . '
            else:
                dot = ''
            drawPageNumbers(canvas, style, [(page, key)], availWidth, availHeight, dot)
        self.canv.drawTOCEntryEnd = drawTOCEntryEnd

        tableData = []
        for entry in _tempEntries:
            level, text, pageNum = entry[:3]
            key = self.refid_lut.get((level, text), None)
            style = self.getLevelStyle(level)
            if key:
                text = '<a href="#%s">%s</a>' % (key, text)
                keyVal = repr(key).replace(',','\\x2c').replace('"','\\x2c')
            else:
                keyVal = None
            para = Paragraph('%s<onDraw name="drawTOCEntryEnd" label="%s,%d,%s"/>' % (text, pageNum, level, keyVal), style)
            if style.spaceBefore:
                tableData.append([Spacer(1, style.spaceBefore),])
            tableData.append([para,])

        self._table = Table(tableData, colWidths=(availWidth,), style=self.tableStyle)

        self.width, self.height = self._table.wrapOn(self.canv,availWidth, availHeight)
        return (self.width, self.height)

genelements.MyTableOfContents = DottedTableOfContents
