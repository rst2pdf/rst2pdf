# -*- coding: utf-8 -*-

"""The user interface for our app"""

import os,sys,tempfile,re
from multiprocessing import Process
from hashlib import md5
from cStringIO import StringIO
from rst2pdf.createpdf import RstToPdf 
from rst2pdf.log import log
import logging

log.setLevel(logging.INFO)

# Import Qt modules
from PyQt4 import QtCore,QtGui
from pypoppler import QtPoppler

# Syntax HL
from highlighter import Highlighter

# Import the compiled UI module
from Ui_main import Ui_MainWindow
from Ui_pdf import Ui_Form

import simplejson as json
from BeautifulSoup import BeautifulSoup

_renderer = RstToPdf(splittables=True)

def render(text, preview=True):
    '''Render text to PDF via rst2pdf'''
    # FIXME: get parameters for this from somewhere
    
    sio=StringIO()
    _renderer.createPdf(text=text, output=sio, debugLinesPdf=preview)
    return sio.getvalue()
    
class Main(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.lineMarks={}

        # This is always the same
        self.ui=Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.pdf=PDFWidget()
        
        self.ui.pageNum = QtGui.QSpinBox()
        self.ui.pageNum.setMinimum(1)
        self.ui.pageNum.setValue(1)
        self.connect(self.pdf,QtCore.SIGNAL('pageCount'),
            self.ui.pageNum.setMaximum)
        self.connect(self.pdf,QtCore.SIGNAL('pageChanged'),
            self.ui.pageNum.setValue)
        self.connect(self.ui.pageNum,QtCore.SIGNAL('valueChanged(int)'),
            self.pdf.gotoPage)

        self.ui.actionShow_ToolBar=self.ui.toolBar.toggleViewAction()
        self.ui.actionShow_ToolBar.setText("Show Main Toolbar")
        self.ui.menuView.addAction(self.ui.actionShow_ToolBar)

        self.ui.pdfbar.addAction(self.pdf.ui.previous)
        self.ui.pdfbar.addWidget(self.ui.pageNum)        
        self.ui.pdfbar.addAction(self.pdf.ui.next)
        self.ui.pdfbar.addSeparator()
        self.ui.pdfbar.addAction(self.pdf.ui.zoomin)
        self.ui.pdfbar.addAction(self.pdf.ui.zoomout)
        self.ui.actionShow_PDFBar=self.ui.pdfbar.toggleViewAction()
        self.ui.actionShow_PDFBar.setText("Show PDF Toolbar")
        self.ui.menuView.addAction(self.ui.actionShow_PDFBar)

        self.ui.dockLayout.addWidget(self.ui.pdfbar)
        self.ui.dockLayout.addWidget(self.pdf)
        self.ui.actionShow_PDF=self.ui.dock.toggleViewAction()
        self.ui.actionShow_PDF.setText('Show Preview')
        self.ui.menuView.addAction(self.ui.actionShow_PDF)
        
        self.text_md5=''
        self.style_md5=''
        
        self.hl1 = Highlighter(self.ui.text.document(),'rest')
        self.hl2 = Highlighter(self.ui.style.document(),'javascript')
        
        self.editorPos=QtGui.QLabel()
        self.ui.statusBar.addWidget(self.editorPos)
        self.editorPos.show()
        
        self.statusMessage=QtGui.QLabel()
        self.ui.statusBar.addWidget(self.statusMessage)
        self.statusMessage.show()
        
        self.on_text_cursorPositionChanged()
        self.on_actionRender_triggered()
        
        self.text_fname=None
        self.style_fname=None
        self.pdf_fname=None

    def createPopupMenu(self):
        self.popup=QtGui.QMenu()
        self.popup.addAction(self.ui.actionShow_ToolBar)
        self.popup.addAction(self.ui.actionShow_PDFBar)
        self.popup.addAction(self.ui.actionShow_PDF)
        return self.popup

    def enableHL(self):
        self.hl1.enabled=True
        self.hl2.enabled=True
        self.hl1.rehighlight()
        self.hl2.rehighlight()

    def disableHL(self):
        self.hl1.enabled=False
        self.hl2.enabled=False

    def on_actionSave_Text_triggered(self, b=None):
        if b is not None: return
        
        if self.text_fname is not None:
            f=open(self.text_fname,'w+')
            f.seek(0)
            f.write(unicode(self.ui.text.toPlainText()))
            f.close()
        else:
            self.on_actionSaveAs_Text_triggered()
            
     
    def on_actionSaveAs_Text_triggered(self, b=None):
        if b is not None: return
        
        fname=unicode(QtGui.QFileDialog.getSaveFileName(self, 
                            'Save As',
                            os.getcwd(),
                            'reSt files (*.txt *.rst)'
                            ))
        if fname:
            self.text_fname=fname
            #self.on_actionSave_Text_triggered()

    def on_actionLoad_Text_triggered(self, b=None):
        if b is None: return
        
        fname=QtGui.QFileDialog.getOpenFileName(self, 
                                                'Open File',
                                                os.getcwd(),
                                                'reSt files (*.txt *.rst)'
                                                )
        self.text_fname=fname
        self.disableHL()
        self.ui.text.setPlainText(open(self.text_fname).read())
        self.enableHL()
        
    def on_actionSave_Style_triggered(self, b=None):
        if b is not None: return
        
        if self.style_fname is not None:
            f=open(self.style_fname,'w+')
            f.seek(0)
            f.write(unicode(self.ui.style.toPlainText()))
            f.close()
        else:
            self.on_actionSaveAs_Style_triggered()
            
     
    def on_actionSaveAs_Style_triggered(self, b=None):
        if b is not None: return
        
        fname=unicode(QtGui.QFileDialog.getSaveFileName(self, 
                            'Save As',
                            os.getcwd(),
                            'style files (*.json *.style)'
                            ))
        if fname:
            self.style_fname=fname
            self.on_actionSave_Style_triggered()


    def on_actionLoad_Style_triggered(self, b=None):
        if b is None: return
        
        fname=QtGui.QFileDialog.getOpenFileName(self, 
                                                'Open File',
                                                os.getcwd(),
                                                'style files (*.json *.style)'
                                                )
        self.style_fname=fname
        self.disableHL()
        self.ui.style.setPlainText(open(self.style_fname).read())
        self.enableHL()
        
    def on_actionSave_PDF_triggered(self, b=None):
        if b is not None: return
        
        # render it without line numbers in the toc
        self.on_actionRender_triggered(preview=False)
            
        if self.pdf_fname is not None:
            f=open(self.pdf_fname,'wb+')
            f.seek(0)
            f.write(self.goodPDF)
            f.close()
        else:
            self.on_actionSaveAs_PDF_triggered()
            
     
    def on_actionSaveAs_PDF_triggered(self, b=None):
        if b is not None: return
        
        fname=unicode(QtGui.QFileDialog.getSaveFileName(self, 
                            'Save As',
                            os.getcwd(),
                            'PDF files (*.pdf)'
                            ))
        if fname:
            self.pdf_fname=fname
            self.on_actionSave_PDF_triggered()

    def on_tabs_currentChanged(self, i):
        if i == 0: 
            self.on_text_cursorPositionChanged()
        else:
            self.on_style_cursorPositionChanged()

    def on_style_cursorPositionChanged(self):
        cursor=self.ui.style.textCursor()
        self.editorPos.setText('Line: %d Col: %d'%(cursor.blockNumber(),cursor.columnNumber()))
        
    def on_text_cursorPositionChanged(self):
        cursor=self.ui.text.textCursor()
        row=cursor.blockNumber()
        column=cursor.columnNumber()
        self.editorPos.setText('Line: %d Col: %d'%(row,column))
        l='line-%s'%(row+1)
        m=self.lineMarks.get(l,None)
        if m:
            self.pdf.gotoPosition(*m)
    def validateStyle(self):
        style=unicode(self.ui.style.toPlainText())
        if not style.strip(): #no point in validating an empty string
            self.statusMessage.setText('')
            return
        pos=None
        try:
            json.loads(style)
            self.statusMessage.setText('')
        except ValueError, e:
            s=str(e)
            if s == 'No JSON object could be decoded':
                pos=0
            elif s.startswith('Expecting '):
                pos=int(s.split(' ')[-1][:-1])
            elif s.startswith('Extra data'):
                pos=int(s.split(' ')[-3])
            else:
                pass
            self.statusMessage.setText('Stylesheet error: %s'%s)
                
        # This makes a red bar appear in the line
        # containing position pos
        self.ui.style.highlightError(pos)
                
    on_style_textChanged = validateStyle
               
    def on_actionRender_triggered(self, b=None, preview=True):
        if b is not None: return
        text=unicode(self.ui.text.toPlainText())
        style=unicode(self.ui.style.toPlainText())
        self.hl1.rehighlight()
        m1=md5()
        m1.update(text.encode('utf-8'))
        m1=m1.digest()
        m2=md5()
        m2.update(style.encode('utf-8'))
        m2=m2.digest()
        
        flag = m1 != self.text_md5
        
        if m2 != self.style_md5 and style:
            fd, style_file=tempfile.mkstemp()
            os.write(fd,style)
            os.close(fd)
            try:
                _renderer.loadStyles([style_file])
                flag = True
            except:
                pass
            os.unlink(style_file)
        if flag:
            if not preview:
                self.goodPDF=render(text, preview=False)
            else:
                self.lastPDF=render(text, preview=preview)
                self.pdf.loadDocument(self.lastPDF)
                toc=self.pdf.document.toc()
                if toc:
                    # TODO: Convert to a python XML thing
                    # then use the LINE-X nodes to sync the PDFDisplay
                    # and the text window :-)
                    xml=unicode(toc.toString())
                    soup=BeautifulSoup(xml)
                    tempMarks=[]
                    # Put all marks in a list and sort them
                    # because they can be repeated and out of order
                    for tag in soup.findAll(re.compile('line-')):
                        dest=QtPoppler.Poppler.LinkDestination(tag['destination'])
                        tempMarks.append([tag.name,[dest.pageNumber(), dest.top(), dest.left(),1.]])
                    tempMarks.sort()
                    
                    self.lineMarks={}
                    lastMark=None
                    #from pudb import set_trace; set_trace()
                    for key,dest in tempMarks:
                        # Fix height of the previous mark, unless we changed pages
                        if lastMark and self.lineMarks[lastMark][0]==dest[0]:
                            self.lineMarks[lastMark][3]=dest[1]
                        # Fill missing lines
                        
                        if lastMark:
                            n1=int(lastMark.split('-')[1])
                            ldest=self.lineMarks[lastMark]
                        else:
                            n1=0
                            ldest=[1,0,0,0]
                        n2=int(key.split('-')[1])
                        for n in range(n1,n2):
                            self.lineMarks['line-%s'%n]=ldest
                        self.lineMarks[key]=dest
                        lastMark = key
        self.on_text_cursorPositionChanged()

def main():
    # Again, this is boilerplate, it's going to be the same on 
    # almost every app you write
    app = QtGui.QApplication(sys.argv)
    window=Main()
    window.show()
    # It's exec_ because exec is a reserved word in Python
    sys.exit(app.exec_())


class PDFWidget(QtGui.QWidget):
    def __init__(self,parent=None):
        QtGui.QWidget.__init__(self,parent)
        self.ui=Ui_Form()
        self.ui.setupUi(self)
        self.pdfd = None
        
    def loadDocument(self,data):
        self.document = QtPoppler.Poppler.Document.loadFromData(data)
        self.emit(QtCore.SIGNAL('pageCount'),self.document.numPages())
        self.document.setRenderHint(QtPoppler.Poppler.Document.Antialiasing and QtPoppler.Poppler.Document.TextAntialiasing)
        
        # When rerendering, keep state as much as possible in 
        # the viewer
        
        if self.pdfd: 
            res = self.pdfd.res
            xpos = self.ui.scroll.horizontalScrollBar().value()
            ypos = self.ui.scroll.verticalScrollBar().value()
            currentPage = self.pdfd.currentPage
        else:
            res=72.
            xpos=0
            ypos=0
            currentPage = 0
        
        self.pdfd=PDFDisplay(self.document)
        self.connect(self.pdfd,QtCore.SIGNAL('pageChanged'),
                     self,QtCore.SIGNAL('pageChanged'))
        self.pdfd.currentPage = currentPage
        self.checkActions()
        self.pdfd.res = res
        self.ui.scroll.setWidget(self.pdfd)
        self.ui.scroll.horizontalScrollBar().setValue(xpos)
        self.ui.scroll.verticalScrollBar().setValue(ypos)
        
    def checkActions(self):
        if not self.pdfd or \
               self.pdfd.currentPage == self.document.numPages():
            self.ui.next.setEnabled(False)
        else:
            self.ui.next.setEnabled(True)
        if not self.pdfd or \
                self.pdfd.currentPage == 1:
            self.ui.previous.setEnabled(False)
        else:
            self.ui.previous.setEnabled(True)
        
    def gotoPosition(self, page, top, left, bottom):
        """The position is defined in terms of poppler's linkdestinations,
        top is in the range 0-1, page is one-based."""
        
        if not self.pdfd:
            return
            
        self.gotoPage(page)
        
        # Draw a mark to see if we are calculating correctly
        pixmap=QtGui.QPixmap(self.pdfd.pdfImage)
        p=QtGui.QPainter(pixmap)
        c=QtGui.QColor(QtCore.Qt.yellow).lighter(160)
        c.setAlpha(150)
        p.setBrush(c)
        p.setPen(c)
        # FIXME, move the highlighting outside
        y1=self.pdfd.pdfImage.height()*top
        y2=self.pdfd.pdfImage.height()*(bottom-top)
        w=self.pdfd.pdfImage.width()
        p.drawRect(0,y1,w,y2)
        self.pdfd.setPixmap(pixmap)
        p.end()
        
        
        
    def gotoPage(self,n):
        if self.pdfd:
            self.pdfd.currentPage = n
        self.checkActions()
        
    def on_next_triggered(self, b=None):
        if b is None: return
        self.pdfd.nextPage()
        self.checkActions()

    def on_previous_triggered(self, b=None):
        if b is None: return
        self.pdfd.prevPage()
        self.checkActions()
        
    def on_zoomin_triggered(self, b=None):
        if b is None: return
        self.pdfd.zoomin()
        
    def on_zoomout_triggered(self, b=None):
        if b is None: return
        self.pdfd.zoomout()
        
            
class PDFDisplay(QtGui.QLabel):
    def __init__(self, doc):
        QtGui.QLabel.__init__(self, None)
        self.doc = doc
        self.pdfImage = None
        self._res = self.physicalDpiX()
        
        self._currentPage = 1
        self.display()

    @property
    def currentPage(self):
        '''The currently displayed page'''
        return self._currentPage
    
    @currentPage.setter
    def currentPage(self,value):
        value=int(value)
        if value != self._currentPage and \
                0 < value <= self.doc.numPages():
            self._currentPage = value
            self.display()
            self.emit(QtCore.SIGNAL('pageChanged'),self._currentPage)

    # Just so I can connect a signal to this
    def setCurrentPage(self,value):
        self.currentPage=value

    def nextPage(self):
        self.currentPage += 1

    def prevPage(self):
        self.currentPage -= 1

    @property
    def res(self):
        '''Display resolution in DPI'''
        return self._res

    @res.setter
    def res(self,value):
        self._res=value
        self.display()

    def zoomin(self):
        self.res=self.res*1.25

    def zoomout(self):
        self.res=self.res/1.25
        
    def display(self):
        if self.doc is not None:
            if self.doc.numPages() == 0:
                self.pdfImage = QtGui.QImage()
            else:
                page = self.doc.page(self.currentPage-1)
                if page:
                    self.pdfImage = None
                    self.pdfImage = page.renderToImage(self.res, self.res)
                    self.resize(self.pdfImage.width(),self.pdfImage.height())
            self.setPixmap(QtGui.QPixmap.fromImage(self.pdfImage))
                #self.update()
                #delete page;

if __name__ == "__main__":
    main()
