# -*- coding: utf-8 -*-

"""The user interface for our app"""

import os,sys,tempfile,re,functools,time,types
from pprint import pprint
from multiprocessing import Process, Queue
from Queue import Empty
from hashlib import md5
from cStringIO import StringIO
from rst2pdf.createpdf import RstToPdf 
from rst2pdf.styles import StyleSheet 
from rst2pdf.log import log
import logging

log.setLevel(logging.INFO)

import docutils

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

StringTypes=types.StringTypes+(QtCore.QString,)


def renderQueue(render_queue, pdf_queue, doctree_queue):
    _renderer = RstToPdf(splittables=True)
    
    def render(doctree, preview=True):
        '''Render text to PDF via rst2pdf'''
        # FIXME: get parameters for this from somewhere

        sio=StringIO()
        _renderer.createPdf(doctree=doctree, output=sio, debugLinesPdf=preview)
        return sio.getvalue()
        
    while True:
        print 'PPID:',os.getppid()
        try:
            style_file, text, preview = render_queue.get(10)
            style_file, text, preview = render_queue.get(False)            
            print 'GOT text to render'
        except Empty: # no more things to render, so do it
            if style_file:
                print 'LOADING StyleSheet'
                _renderer.loadStyles([style_file])
            flag = True
            #os.unlink(style_file)
            print 'PARSING',time.time()
            doctree = docutils.core.publish_doctree(text)
            doctree_queue.put(doctree)
            print 'PARSED',time.time()    
            pdf_queue.put(render(doctree, preview))
        if os.getppid()==1: # Parent died
            sys.exit(0)
      
    
class Main(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        
        self.doctree=None
        self.lineMarks={}

        # We put things we want rendered here
        self.render_queue = Queue()
        # We get things rendered back
        self.pdf_queue = Queue()
        # We get doctrees for the outline viewer
        self.doctree_queue = Queue()
        
        print 'Starting background renderer...',
        self.renderProcess=Process(target = renderQueue, 
            args=(self.render_queue, self.pdf_queue, self.doctree_queue))
        self.renderProcess.daemon=True
        self.renderProcess.start()
        print 'DONE'
        
        # This is always the same
        self.ui=Ui_MainWindow()
        self.ui.setupUi(self)

        # Adjust column widths in the structure tree
        self.ui.tree.header().setStretchLastSection(False)
        self.ui.tree.header().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.ui.tree.header().setResizeMode(1, QtGui.QHeaderView.ResizeToContents)

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
        self.ui.dock.hide()
        self.ui.actionShow_PDF=self.ui.dock.toggleViewAction()
        self.ui.actionShow_PDF.setText('Show Preview')
        self.ui.menuView.addAction(self.ui.actionShow_PDF)
        self.ui.actionShow_Structure=self.ui.structure.toggleViewAction()
        self.ui.actionShow_Structure.setText('Show Document Outline')
        self.ui.menuView.addAction(self.ui.actionShow_Structure)
        
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

        # Connect editing actions to the editors
        self.ui.text.undoAvailable.connect(self.ui.actionUndo1.setEnabled)
        self.ui.actionUndo1.triggered.connect(self.ui.text.undo)
        self.ui.text.redoAvailable.connect(self.ui.actionRedo1.setEnabled)
        self.ui.actionRedo1.triggered.connect(self.ui.text.redo)
        
        self.ui.text.copyAvailable.connect(self.ui.actionCopy1.setEnabled)
        self.ui.actionCopy1.triggered.connect(self.ui.text.copy)
        self.ui.text.copyAvailable.connect(self.ui.actionCut1.setEnabled)
        self.ui.actionCut1.triggered.connect(self.ui.text.cut)
        self.ui.actionPaste1.triggered.connect(self.ui.text.paste)
        

        self.ui.style.undoAvailable.connect(self.ui.actionUndo2.setEnabled)
        self.ui.actionUndo2.triggered.connect(self.ui.style.undo)
        self.ui.style.redoAvailable.connect(self.ui.actionRedo2.setEnabled)
        self.ui.actionRedo2.triggered.connect(self.ui.style.redo)
        
        self.ui.style.copyAvailable.connect(self.ui.actionCopy2.setEnabled)
        self.ui.actionCopy2.triggered.connect(self.ui.style.copy)
        self.ui.style.copyAvailable.connect(self.ui.actionCut2.setEnabled)
        self.ui.actionCut2.triggered.connect(self.ui.style.cut)
        self.ui.actionPaste2.triggered.connect(self.ui.style.paste)
        
        self.clipBoard=QtGui.QApplication.clipboard()
        self.clipBoard.changed.connect(self.clipChanged)
        
        self.hookEditToolbar(self.ui.text)
        self.clipChanged(QtGui.QClipboard.Clipboard)
        
        self.text_fname=None
        self.style_fname=None
        self.pdf_fname=None

        self.ui.searchbar.setVisible(False)
        self.ui.searchWidget=SearchWidget()
        self.ui.searchbar.addWidget(self.ui.searchWidget)
        self.ui.actionFind.triggered.connect(self.ui.searchbar.show)
        self.ui.actionFind.triggered.connect(self.ui.searchWidget.ui.text.setFocus)
        self.ui.searchWidget.ui.close.clicked.connect(self.ui.searchbar.hide)
        self.ui.searchWidget.ui.close.clicked.connect(self.returnFocus)
        self.ui.searchWidget.ui.next.clicked.connect(self.doFind)
        self.ui.searchWidget.ui.previous.clicked.connect(self.doFindBackwards)
    
        self.updatePdf()
        
        self.renderTimer=QtCore.QTimer()
        self.renderTimer.timeout.connect(self.on_actionRender_triggered)
        self.renderTimer.start(5000)

    def returnFocus(self):
        """after the search bar closes, focus on the editing widget"""
        print 'RF:', self.ui.tabs.currentIndex()
        if self.ui.tabs.currentIndex()==0:
            self.ui.text.setFocus()
        else:
            self.ui.style.setFocus()

    def doFindBackwards (self):
        return self.doFind(backwards=True)
    
    def doFind(self, backwards=False):

        flags=QtGui.QTextDocument.FindFlags()
        print flags
        if backwards:
            flags=QtGui.QTextDocument.FindBackward
        if self.ui.searchWidget.ui.matchCase.isChecked():
            flags=flags|QtGui.QTextDocument.FindCaseSensitively

        text=unicode(self.ui.searchWidget.ui.text.text())
        
        print 'Serching for:',text
        
        if self.ui.tabs.currentIndex()==0:
            r=self.ui.text.find(text,flags)
        else:
            r=self.ui.style.find(text,flags)
        if r:
            self.statusMessage.setText('')
        else:
            self.statusMessage.setText('%s not found'%text)

    def clipChanged(self, mode=None):
        if mode is None: return
        if mode == QtGui.QClipboard.Clipboard:
            if unicode(self.clipBoard.text()):
                self.ui.actionPaste1.setEnabled(True)
                self.ui.actionPaste2.setEnabled(True)
            else:
                self.ui.actionPaste1.setEnabled(False)
                self.ui.actionPaste2.setEnabled(False)

    def hookEditToolbar(self, editor):
        if editor == self.ui.text:
            self.ui.actionUndo2.setVisible(False)
            self.ui.actionRedo2.setVisible(False)
            self.ui.actionCut2.setVisible(False)
            self.ui.actionPaste2.setVisible(False)
            self.ui.actionCopy2.setVisible(False)
            self.ui.actionUndo1.setVisible(True)
            self.ui.actionRedo1.setVisible(True)
            self.ui.actionCut1.setVisible(True)
            self.ui.actionPaste1.setVisible(True)
            self.ui.actionCopy1.setVisible(True)
        else:
            self.ui.actionUndo1.setVisible(False)
            self.ui.actionRedo1.setVisible(False)
            self.ui.actionCut1.setVisible(False)
            self.ui.actionPaste1.setVisible(False)
            self.ui.actionCopy1.setVisible(False)
            self.ui.actionUndo2.setVisible(True)
            self.ui.actionRedo2.setVisible(True)
            self.ui.actionCut2.setVisible(True)
            self.ui.actionPaste2.setVisible(True)
            self.ui.actionCopy2.setVisible(True)
       

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

    def on_actionTest_Action_triggered(self, b=None):
        if b is not None: return
        
        
        # I need to create a stylesheet object so I can parse and merge
        # the current stylesheet
        
        # FIXME: passing the current stylesheet to the StyleSheet class
        # should be much simpler than this, also it's repeated from
        # another method
        # TODO: don't use the current user stylesheet if it's not valid!
        style=unicode(self.ui.style.toPlainText())
        fd, style_file=tempfile.mkstemp()
        os.write(fd,style)
        os.close(fd)
        self.styles = StyleSheet([style_file])
        os.unlink(style_file)

        self.testwidget=PageTemplates(self.styles)
        self.testwidget.show()


    def on_tree_itemClicked(self, item=None, column=None):
        if item is None: return
        
        destline=int(item.text(1))-1
        destblock=self.ui.text.document().findBlockByLineNumber(destline)
        cursor=self.ui.text.textCursor()
        cursor.setPosition(destblock.position())
        self.ui.text.setTextCursor(cursor)
        self.ui.text.ensureCursorVisible()

    def on_actionAbout_Bookrest_triggered(self, b=None):
        if b is None: return
        dlg=AboutDialog()
        dlg.exec_()

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

    def on_tabs_currentChanged(self, i=None):
        print 'IDX:',self.ui.tabs.currentIndex()
        if self.ui.tabs.currentIndex() == 0: 
            self.on_text_cursorPositionChanged()
            print 'hooking text editor'
            self.hookEditToolbar(self.ui.text)
        else:
            self.on_style_cursorPositionChanged()
            print 'hooking style editor'
            self.hookEditToolbar(self.ui.style)

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
        style_file=None
        if m2 != self.style_md5 and style:
            fd, style_file=tempfile.mkstemp()
            os.write(fd,style)
            os.close(fd)
            print 'Loading styles from style_file'
            flag = True
        if flag:
            if not preview:
                pass
                # Send text to the renderer in foreground
                # FIXME: render is no longer accessible from the parent
                # process
                #doctree = docutils.core.publish_doctree(text)
                #self.goodPDF=render(doctree, preview=False)
            else:
                # Que to render in background
                self.render_queue.put([style_file, text, preview])
                self.text_md5=m1
                self.style_md5=m2

    def updatePdf(self):
        
        # See if there is something in the doctree Queue
        try:
            self.doctree=self.doctree_queue.get(False)
            self.doctree.reporter=log
            class Visitor(docutils.nodes.SparseNodeVisitor):
                
                def __init__(self, document, treeWidget):
                    self.treeWidget=treeWidget
                    self.treeWidget.clear()
                    self.doctree=document
                    self.nodeDict={}
                    docutils.nodes.SparseNodeVisitor.__init__(self, document)
                
                def visit_section(self, node):
                    print 'SECTION:',node.line,
                    item=QtGui.QTreeWidgetItem(["",str(node.line)])
                    if node.parent==self.doctree:
                        # Top level section
                        self.treeWidget.addTopLevelItem(item)
                        self.nodeDict[id(node)]=item
                    else:
                        self.nodeDict[id(node.parent)].addChild(item)
                        self.nodeDict[id(node)]=item
                    
                def visit_title(self, node):
                    if id(node.parent) in self.nodeDict:
                        self.nodeDict[id(node.parent)].setText(0,node.astext())
                    
                def visit_document(self,node):
                    print 'DOC:',node.line
                    
            print self.doctree.__class__
            self.visitor=Visitor(self.doctree, self.ui.tree)
            self.doctree.walkabout(self.visitor)
            print self.visitor.nodeDict
            
        except Empty:
            pass
        
        # See if there is something in the PDF Queue
        try:
            self.lastPDF=self.pdf_queue.get(False)
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
                    tempMarks.append([int(tag.name.split('-')[1]),[dest.pageNumber(), dest.top(), dest.left(),1.]])
                tempMarks.sort()
                
                self.lineMarks={}
                lastMark=None
                lastKey=0
                for key,dest in tempMarks:
                    # Fix height of the previous mark, unless we changed pages
                    if lastMark and self.lineMarks[lastMark][0]==dest[0]:
                        self.lineMarks[lastMark][3]=dest[1]
                    # Fill missing lines
                    
                    if lastMark:
                        ldest=self.lineMarks[lastMark]
                    else:
                        ldest=[1,0,0,0]
                    for n in range(lastKey,key):
                        self.lineMarks['line-%s'%n]=ldest
                    k='line-%s'%key
                    self.lineMarks[k]=dest
                    lastMark = k
                    lastKey = key
                    
            self.on_text_cursorPositionChanged()
        except Empty: #Nothing there
            pass
        
        # Schedule to run again
        QtCore.QTimer.singleShot(500,self.updatePdf)
        

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

# Firefox-style in-window search widget, 
# copied from uRSSus: http://urssus.googlecode.com
from Ui_searchwidget import Ui_Form as UI_SearchWidget

class SearchWidget(QtGui.QWidget):
  def __init__(self):
    QtGui.QWidget.__init__(self)
    # Set up the UI from designer
    self.ui=UI_SearchWidget()
    self.ui.setupUi(self)

# Cute about dialog
from Ui_about import Ui_Dialog as Ui_AboutDialog


class AboutDialog(QtGui.QDialog):
  def __init__(self):
    QtGui.QDialog.__init__(self)
    # Set up the UI from designer
    self.ui=Ui_AboutDialog()
    self.ui.setupUi(self)

# Widget to edit page templates
from Ui_pagetemplates import Ui_Form as Ui_templates


class PageTemplates(QtGui.QWidget):
    def __init__(self, stylesheet, parent=None):
        QtGui.QWidget.__init__(self,parent)
        self.ui=Ui_templates()
        self.ui.setupUi(self)
        self.stylesheet = stylesheet
        self.pw=self.stylesheet.ps[0]
        self.ph=self.stylesheet.ps[1]
        self.pageImage=QtGui.QImage(int(self.pw),
                                    int(self.ph),
                                    QtGui.QImage.Format_RGB32)
        self.template = None
        for template in self.stylesheet.pageTemplates:
            self.ui.templates.addItem(template)
        self.updatePreview()

    def on_templates_currentIndexChanged(self, text):
        if not isinstance(text,StringTypes): return
        text=unicode(text)
        self.template=self.stylesheet.pageTemplates[text]
        self.ui.frames.clear()
        for i in range(0, len(self.template['frames'])):
            self.ui.frames.addItem('Frame %d'%(i+1))
        self.ui.footer.setChecked(self.template['showFooter'])
        self.ui.header.setChecked(self.template['showHeader'])
        
        self.updatePreview()
        
    def on_frames_currentIndexChanged(self, index):
        if type(index) != types.IntType: return
        if not self.template: return
        self.frame=self.template['frames'][index]
        self.ui.top.setText(self.frame[0])
        self.ui.left.setText(self.frame[1])
        self.ui.width.setText(self.frame[2])
        self.ui.height.setText(self.frame[3])
        self.updatePreview()
    
    def updatePreview(self):
        pm=QtGui.QPixmap(self.pageImage)
        p=QtGui.QPainter(pm)
        p.setBrush(QtGui.QBrush(QtGui.QColor("white")))
        p.drawRect(-1,-1,pm.width()+2,pm.height()+2)
        
        def drawFrame(frame):
            x=self.stylesheet.adjustUnits(frame[0],self.pw)
            y=self.stylesheet.adjustUnits(frame[1],self.ph)
            w=self.stylesheet.adjustUnits(frame[2],self.pw)-1
            h=self.stylesheet.adjustUnits(frame[3],self.ph)-1
            p.drawRect(x,y,w,h)
        
        p.setBrush(QtGui.QBrush(QtGui.QColor("lightgrey")))
        for frame in self.template['frames']:
            drawFrame(frame)
        p.setBrush(QtGui.QBrush(QtGui.QColor("yellow")))
        drawFrame(self.frame)    
        p.end()
        self.ui.preview.setPixmap(pm)

if __name__ == "__main__":
    main()

