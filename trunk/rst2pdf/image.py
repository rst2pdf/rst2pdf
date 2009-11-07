# -*- coding: utf-8 -*-

import os
import tempfile
from copy import copy
from reportlab.platypus.flowables import Image, Flowable
from log import log, nodeid
from reportlab.lib.units import *

from opt_imports import PMImage, PILImage

HAS_MAGICK = PMImage is not None
HAS_PIL = PILImage is not None

if not HAS_MAGICK and not HAS_PIL:
    log.warning("Support for images other than JPG,"
        " is now limited. Please install PIL.")

from svgimage import SVGImage, VectorImage

missing = os.path.join(os.path.join(os.path.abspath(os.path.dirname(__file__))), 
          'images', 'image-missing.jpg')

class MyImage (Flowable):
    """A Image subclass that can:
    
    1. Take a 'percentage_of_container' kind,
       which resizes it on wrap() to use... well, a percentage of the
       container's width.

    2. Take vector formats and instantiates the right "backend" flowable
    
    """

    def __init__(self, filename, width=None, height=None,
                 kind='direct', mask="auto", lazy=1, client=None):
        self.__kind=kind
        
        self.filename, self._backend=self.get_backend(filename, client)
        if kind == 'percentage_of_container':
            self.image=self._backend(self.filename, width, height,
                'direct', mask, lazy)
            self.image.drawWidth=width
            self.image.drawHeight=height
            self.__width=width
            self.__height=height
        else:
            self.image=self._backend(self.filename, width, height,
                kind, mask, lazy)
        self.__ratio=float(self.image.imageWidth)/self.image.imageHeight
        self.__wrappedonce=False

    @classmethod
    def raster(self, filename, client):
	"""Takes a filename and converts it to a raster image
        reportlab can process"""
        if not os.path.exists(filename):
            log.error("Missing image file: %s",filename)
            return missing

	if HAS_PIL:
	    ext='.png'
	else:
	    ext='.jpg'

        extension = os.path.splitext(filename)[-1][1:].lower()
        
        if HAS_PIL: # See if pil can process it
            try:
                PILImage().open(filename)
                return filename
            except:
                # Can't read it
                pass

        # PIL can't or isn't here, so try with Magick

        if HAS_MAGICK:
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
        # PIL can't and Magick can't, so we can't
        log.error("Couldn't load image [%s]"%filename)
        return missing


    @classmethod
    def get_backend(self,filename, client):
        '''Given the filename of an image, returns (fname, backend)
        where fname is the filename to be used (could be the same as
        filename, or something different if the image had to be converted
        or is missing), and backend is an Image class that can handle 
        fname.'''

        # If the image doesn't exist, we use a 'missing' image
        if not os.path.exists(filename):
            log.error("Missing image file: %s",filename)
            filename = missing

        # Decide what class of backend image we will use
        extension = os.path.splitext(filename)[-1][1:].lower()
        
        if extension in ['svg','svgz'] and SVGImage.available():
            backend=SVGImage
        
        elif extension in ['ai', 'ccx', 'cdr', 'cgm', 'cmx', 'fig',
                'sk1', 'sk', 'xml', 'wmf']:
            backend=VectorImage
            
        elif extension in ['pdf']:
            # PDF images are implemented by converting via PythonMagick
            # w,h are in pixels. I need to set the density
            # of the image to  the right dpi so this
            # looks decent
            if HAS_MAGICK:
                filename=self.raster(filename, client)
                backend=Image
            else:
                log.warning("Minimal PDF image support "\
                    "requires PythonMagick [%s]", filename)
                filename = missing
        elif not HAS_PIL and HAS_MAGICK and extension != 'jpg':
            # Need to convert to JPG via PythonMagick
            filename=self.raster(filename)
            backend=Image
            
        elif HAS_PIL or extension == 'jpg':
            backend=Image
        else:
            # No way to make this work
            log.error('To use a %s image you need PIL installed [%s]',extension,filename)
            backend=Image
            filename=missing
        return filename, backend


    @classmethod
    def size_for_node(self, node, client):
        '''Given a docutils image node, returns the size the image should have
        in the PDF document, and what 'kind' of size that is. 
        That involves lots of guesswork'''
        
        imgname = os.path.join(client.basedir,str(node.get("uri")))
        
        if not os.path.isfile(imgname):
            imgname = missing
            
        scale = float(node.get('scale', 100))/100

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
            iw, ih = SVGImage(imgname).wrap(0, 0)
            # These are in pt, so convert to px
            iw = iw * xdpi / 72
            ih = ih * ydpi / 72
            
        elif extension in [
                "ai", "ccx", "cdr", "cgm", "cmx",
                "sk1", "sk", "xml", "wmf", "fig"] and VectorImage.available():
            iw, ih = VectorImage(imgname).wrap(0, 0)
            # These are in pt, so convert to px
            iw = iw * xdpi / 72
            ih = ih * ydpi / 72
                    
        elif extension == 'pdf':
            try:
                from pyPdf import pdf
            except:
                log.warning('PDF images are not supported without pypdf [%s]', nodeid(node))
                return 0, 0, 'direct'
            reader = pdf.PdfFileReader(open(imgname))
            x1, y1, x2, y2 = reader.getPage(0)['/MediaBox']
            # These are in pt, so convert to px
            iw = float((x2-x1) * xdpi / 72)
            ih = float((y2-y1) * ydpi / 72)
            
        else:
            if HAS_PIL:
                img = PILImage.open(imgname)
                iw, ih = img.size
                xdpi, ydpi = img.info.get('dpi', (xdpi, ydpi))
            elif HAS_MAGICK:
                img = PMImage(imgname)
                iw = img.size().width()
                ih = img.size().height()
		density=img.density() 
		# The density is in pixelspercentimeter (!?)
		xdpi=density.width()*2.54
		ydpi=density.height()*2.54
            else:
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
            log.warning("Using image %s without specifying size."
                "Calculating based on image size at %ddpi [%s]",
                imgname, xdpi, nodeid(node))
            # No width specified at all, use w in px
            w = iw*inch/xdpi

        h = node.get('height')
        if h is not None and h[-1] != '%':
            h = client.styles.adjustUnits(h, ih*inch/ydpi)
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
                if not self._atTop:
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
        
