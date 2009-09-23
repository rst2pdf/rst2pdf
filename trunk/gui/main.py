# -*- coding: utf-8 -*-

"""The user interface for our app"""

import os,sys,tempfile
from multiprocessing import Process
from hashlib import md5
from cStringIO import StringIO
from rst2pdf.createpdf import RstToPdf 

# Import Qt modules
from PyQt4 import QtCore,QtGui
from pypoppler import QtPoppler

# from reSTinPeace
from highlighter import Highlighter

# Import the compiled UI module
from Ui_main import Ui_MainWindow
from Ui_pdf import Ui_Form

import simplejson as json

_renderer = RstToPdf(splittables=True)

def render(text):
    '''Render text to PDF via rst2pdf'''
    # FIXME: get parameters for this from somewhere
    
    sio=StringIO()
    _renderer.createPdf(text=text, output=sio)
    return sio.getvalue()
    
class Main(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        
        # This is always the same
        self.ui=Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.pdf=PDFWidget()
        self.ui.dock.setWidget(self.pdf)
        self.ui.pdfbar.addAction(self.pdf.ui.previous)
        
        self.ui.pageNum = QtGui.QSpinBox()
        self.ui.pageNum.setMinimum(1)
        self.ui.pageNum.setValue(1)
        self.connect(self.pdf,QtCore.SIGNAL('pageCount'),
            self.ui.pageNum.setMaximum)
        self.connect(self.pdf,QtCore.SIGNAL('pageChanged'),
            self.ui.pageNum.setValue)
        self.connect(self.ui.pageNum,QtCore.SIGNAL('valueChanged(int)'),
            self.pdf.gotoPage)
        self.ui.pdfbar.addWidget(self.ui.pageNum)
        
        self.ui.pdfbar.addAction(self.pdf.ui.next)
        self.ui.pdfbar.addSeparator()
        self.ui.pdfbar.addAction(self.pdf.ui.zoomin)
        self.ui.pdfbar.addAction(self.pdf.ui.zoomout)

        self.ui.actionShow_PDF=self.ui.dock.toggleViewAction ()
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
        
        # Adjust the QSciScintillas
        #for w in self.ui.text, self.ui.style:
            #w.setMarginLineNumbers(1,True)
            #w.setMarginWidth(1,"9999")
            #w.markerDefine('>',1)

        self.on_text_cursorPositionChanged()
        self.on_actionRender_triggered()
        
        self.text_fname=None
        self.style_fname=None
        self.pdf_fname=None

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
            self.on_actionSave_Text_triggered()

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
        
        if not self.lastPDF:
            self.on_actionRender_triggered()
            
        if self.pdf_fname is not None:
            f=open(self.pdf_fname,'wb+')
            f.seek(0)
            f.write(self.lastPDF)
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
        self.editorPos.setText('Line: %d Col: %d'%(cursor.blockNumber(),cursor.columnNumber()))
        
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
               
    def on_actionRender_triggered(self, b=None):
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
            self.lastPDF=render(text)
            self.pdf.loadDocument(self.lastPDF)

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
        self._res = 72.0
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
