# -*- coding: utf-8 -*-

import os
from os.path import abspath, dirname, expanduser, join
import sys
import tempfile
from copy import copy
from reportlab.platypus.flowables import Image, Flowable
from log import log, nodeid
from reportlab.lib.units import *

from opt_imports import LazyImports

from svgimage import SVGImage, VectorImage

# This assignment could be overridden by an extension module
VectorPdf = None

# find base path
if hasattr(sys, 'frozen'):
    PATH = abspath(dirname(sys.executable))
else:
    PATH = abspath(dirname(__file__))

missing = os.path.join(PATH, 'images', 'image-missing.jpg')

def defaultimage(filename, width=None, height=None, kind='direct',
                                        mask="auto", lazy=1, srcinfo=None):
    ''' We have multiple image backends, including the stock reportlab one.
        This wrapper around the reportlab one allows us to pass the client
        RstToPdf object and the uri into all our backends, which they can
        use or not as necessary.
    '''
    return Image(filename, width, height, kind, mask, lazy)

class MyImage (Flowable):
    """A Image subclass that can:
    
    1. Take a 'percentage_of_container' kind,
       which resizes it on wrap() to use... well, a percentage of the
       container's width.

    2. Take vector formats and instantiates the right "backend" flowable
    
    """

    warned = False

    @classmethod
    def support_warning(cls):
        if cls.warned or LazyImports.PILImage:
            return
        cls.warned = True
        log.warning("Support for images other than JPG,"
            " is now limited. Please install PIL.")

    @staticmethod
    def split_uri(uri):
        ''' A really minimalistic split -- doesn't cope with http:, etc.
            HOWEVER, it tries to do so in a fashion that allows a clueless
            user to have '#' inside his filename without screwing anything
            up.
        '''
        basename, extra = os.path.splitext(uri)
        extra = extra.split('#', 1) + ['']
        fname = basename + extra[0]
        extension = extra[0][1:].lower()
        options = extra[1]
        return fname, extension, options

    def __init__(self, filename, width=None, height=None,
                 kind='direct', mask="auto", lazy=1, client=None):
        # Client is mandatory.  Perhaps move it farther up if we refactor
        assert client is not None
        srcinfo = client, filename
        self.__kind=kind
        self.filename, self._backend=self.get_backend(filename, client)
        if kind == 'percentage_of_container':
            self.image=self._backend(self.filename, width, height,
                'direct', mask, lazy, srcinfo)
            self.image.drawWidth=width
            self.image.drawHeight=height
            self.__width=width
            self.__height=height
        else:
            self.image=self._backend(self.filename, width, height,
                kind, mask, lazy, srcinfo)
        self.__ratio=float(self.image.imageWidth)/self.image.imageHeight
        self.__wrappedonce=False

    @classmethod
    def raster(self, filename, client):
        """Takes a filename and converts it to a raster image
        reportlab can process"""
        if not os.path.exists(filename):
            log.error("Missing image file: %s",filename)
            return missing

        PILImage = LazyImports.PILImage

        if PILImage:
            ext='.png'
        else:
            ext='.jpg'

        extension = os.path.splitext(filename)[-1][1:].lower()
        
        if PILImage: # See if pil can process it
            try:
                PILImage.open(filename)
                return filename
            except:
                # Can't read it
                pass

        # PIL can't or isn't here, so try with Magick

        PMImage = LazyImports.PMImage
        if PMImage:
            try:
                img = PMImage()
                # Adjust density to pixels/cm
                dpi=client.styles.def_dpi
                img.density("%sx%s"%(dpi,dpi))
                img.read(str(filename))
                _, tmpname = tempfile.mkstemp(suffix=ext)
                img.write(tmpname)
                client.to_unlink.append(tmpname)
                return tmpname
            except:
                # Magick couldn't
                pass
        elif PILImage:
            # Try to use gfx, which produces PNGs, and then
            # pass them through PIL.
            # This only really matters for PDFs but it's worth trying
            gfx = LazyImports.gfx
            try:
                # Need to convert the DPI to % where 100% is 72DPI
                gfx.setparameter( "zoom", str(client.styles.def_dpi/.72))
                if extension == 'pdf':
                    doc = gfx.open("pdf", filename)
                elif extension == 'swf':
                    doc = gfx.open("swf", filename)
                else:
                    doc = None
                if doc:
                    img = gfx.ImageList()
                    img.setparameter("antialise", "1") # turn on antialising    
                    page = doc.getPage(1)
                    img.startpage(page.width,page.height)
                    page.render(img)
                    img.endpage()
                    _, tmpname = tempfile.mkstemp(suffix='.png')
                    img.save(tmpname)
                    client.to_unlink.append(tmpname)
                    return tmpname
            except: # Didn't work
                pass
            
        # PIL can't and Magick can't, so we can't
        self.support_warning()
        log.error("Couldn't load image [%s]"%filename)
        return missing


    @classmethod
    def get_backend(self, uri, client):
        '''Given the filename of an image, returns (fname, backend)
        where fname is the filename to be used (could be the same as
        filename, or something different if the image had to be converted
        or is missing), and backend is an Image class that can handle 
        fname.'''

        backend = defaultimage

        # Extract all the information from the URI
        filename, extension, options = self.split_uri(uri)

        # If the image doesn't exist, we use a 'missing' image
        if not os.path.exists(filename):
            log.error("Missing image file: %s",filename)
            filename = missing

        if extension in ['svg','svgz']:
            if SVGImage.available():
                log.info('Backend for %s is SVGIMage'%filename)
                backend=SVGImage
            else:
                filename = missing
        
        elif extension in ['ai', 'ccx', 'cdr', 'cgm', 'cmx', 'fig',
                'sk1', 'sk', 'xml', 'wmf']:
            log.info('Backend for %s is VectorImage'%filename)
            backend=VectorImage
            
        elif extension in ['pdf']:
            if VectorPdf is not None and filename is not missing:
                backend = VectorPdf
                filename = uri

            # PDF images are implemented by converting via PythonMagick
            # w,h are in pixels. I need to set the density
            # of the image to  the right dpi so this
            # looks decent
            elif LazyImports.PMImage or LazyImports.gfx:
                filename=self.raster(filename, client)
            else:
                log.warning("Minimal PDF image support "\
                    "requires PythonMagick [%s]", filename)
                filename = missing
        elif extension != 'jpg' and not LazyImports.PILImage:
            if LazyImports.PMImage:
                # Need to convert to JPG via PythonMagick
                filename=self.raster(filename)
            else:
                # No way to make this work
                log.error('To use a %s image you need PIL installed [%s]',extension,filename)
                filename=missing
        return filename, backend


    @classmethod
    def size_for_node(self, node, client):
        '''Given a docutils image node, returns the size the image should have
        in the PDF document, and what 'kind' of size that is. 
        That involves lots of guesswork'''
        
        uri = os.path.join(client.basedir,str(node.get("uri")))
        srcinfo = client, uri
        
        # Extract all the information from the URI
        imgname, extension, options = self.split_uri(uri)

        if not os.path.isfile(imgname):
            imgname = missing
            
        scale = float(node.get('scale', 100))/100
        size_known = False

        # Figuring out the size to display of an image is ... annoying.
        # If the user provides a size with a unit, it's simple, adjustUnits
        # will return it in points and we're done.

        # However, often the unit wil be "%" (specially if it's meant for
        # HTML originally. In which case, we will use a percentage of
        # the containing frame.

        # Find the image size in pixels:
        kind = 'direct'
        xdpi, ydpi = client.styles.def_dpi, client.styles.def_dpi
        extension = imgname.split('.')[-1].lower()
        if extension in ['svg','svgz'] and SVGImage.available():
            iw, ih = SVGImage(imgname, srcinfo=srcinfo).wrap(0, 0)
            # These are in pt, so convert to px
            iw = iw * xdpi / 72
            ih = ih * ydpi / 72
            
        elif extension in [
                "ai", "ccx", "cdr", "cgm", "cmx",
                "sk1", "sk", "xml", "wmf", "fig"] and VectorImage.available():
            iw, ih = VectorImage(imgname, srcinfo=srcinfo).wrap(0, 0)
            # These are in pt, so convert to px
            iw = iw * xdpi / 72
            ih = ih * ydpi / 72
                    
        elif extension == 'pdf':
            if VectorPdf is not None:
                box = VectorPdf.load_xobj(srcinfo).BBox
            else:
                pdf = LazyImports.pdfinfo
                if pdf is None:
                    log.warning('PDF images are not supported without pyPdf or pdfrw [%s]', nodeid(node))
                    return 0, 0, 'direct'
                reader = pdf.PdfFileReader(open(imgname, 'rb'))
                box = [float(x) for x in reader.getPage(0)['/MediaBox']]
            x1, y1, x2, y2 = box
            # These are in pt, so convert to px
            iw = float((x2-x1) * xdpi / 72)
            ih = float((y2-y1) * ydpi / 72)
            size_known = True  # Assume size from original PDF is OK
            
        else:
            keeptrying = True
            
            if LazyImports.PILImage:
                try:
                    img = LazyImports.PILImage.open(imgname)
                    img.load()
                    iw, ih = img.size
                    xdpi, ydpi = img.info.get('dpi', (xdpi, ydpi))
                    keeptrying = False
                except IOError: # PIL throws this when it's a broken/unknown image
                    pass
            if keeptrying and LazyImports.PMImage:
                img = LazyImports.PMImage(imgname)
                iw = img.size().width()
                ih = img.size().height()
                density=img.density() 
                # The density is in pixelspercentimeter (!?)
                xdpi=density.width()*2.54
                ydpi=density.height()*2.54
                keeptrying = False
            if keeptrying:
                log.warning("Sizing images without PIL "
                            "or PythonMagick, using 100x100 [%s]"
                            , nodeid(node))
                iw, ih = 100., 100.

        # Try to get the print resolution from the image itself via PIL.
        # If it fails, assume a DPI of 300, which is pretty much made up,
        # and then a 100% size would be iw*inch/300, so we pass
        # that as the second parameter to adjustUnits
        #
        # Some say the default DPI should be 72. That would mean
        # the largest printable image in A4 paper would be something
        # like 480x640. That would be awful.
        #

        w = node.get('width')
        if w is not None:
            # In this particular case, we want the default unit
            # to be pixels so we work like rst2html
            if w[-1] == '%':
                kind = 'percentage_of_container'
                w=int(w[:-1])
            else:
                # This uses default DPI setting because we
                # are not using the image's "natural size"
                # this is what LaTeX does, according to the
                # docutils mailing list discussion
                w = client.styles.adjustUnits(w, client.styles.tw,
                                            default_unit='px')
        else:
            if not size_known:
                log.warning("Using image %s without specifying size."
                    "Calculating based on image size at %ddpi [%s]",
                    imgname, xdpi, nodeid(node))
            # No width specified at all, use w in px
            w = iw*inch/xdpi

        h = node.get('height')
        if h is not None and h[-1] != '%':
            h = client.styles.adjustUnits(h, ih*inch/ydpi, default_unit='px')
        else:
            # Now, often, only the width is specified!
            # if we don't have a height, we need to keep the
            # aspect ratio, or else it will look ugly
            if h and h[-1]=='%':
                log.error('Setting height as a percentage does **not** work. '\
                          'ignoring height parameter [%s]', nodeid(node))
            h = w*ih/iw

        # Apply scale factor
        w = w*scale
        h = h*scale

        # And now we have this probably completely bogus size!
        log.info("Image %s size calculated:  %fcm by %fcm [%s]",
            imgname, w/cm, h/cm, nodeid(node))

        return w, h, kind
        

    def __deepcopy__(self, *whatever):
        # ImageCore class is not deep copyable.  Stop the copy at this
        # class.  If you remove this, re-test for issue #126.
        return copy(self)

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
            self.image.drawWidth, self.image.drawHeight = w, h
            return w, h
        else:
            if self.image.drawHeight > availHeight:
                if not getattr(self, '_atTop', True):
                    return self.image.wrap(availWidth, availHeight)
                else:
                    # It's the first thing in the frame, probably
                    # Wrapping it will not make it work, so we
                    # adjust by height
                    # FIXME get rst file info (line number)
                    # here for better error message
                    log.warning('image %s is too tall for the '\
                                'frame, rescaling'%\
                                self.filename)
                    self.image.drawHeight = availHeight
                    self.image.drawWidth = availHeight*self.__ratio
            elif self.image.drawWidth > availWidth:
                log.warning('image %s is too wide for the frame, rescaling'%\
                            self.filename)
                self.image.drawWidth = availWidth
                self.image.drawHeight = availWidth / self.__ratio
            return self.image.wrap(availWidth, availHeight)
    
    def drawOn(self, canv, x, y, _sW=0):
        return self.image.drawOn(canv, x, y, _sW)
        
