import re

from docutils.nodes import General, Inline, Element, image
from docutils.parsers import rst
from docutils.parsers.rst.directives.images import Image

from reportlab.lib import colors, units
from reportlab.graphics.barcode import createBarcodeDrawing, eanbc
from log import log

# utilities
to_camelcase = lambda s: re.sub(r'([^_]+)_([a-z])', lambda m: m.expand(r'\1')+m.expand(r'\2').upper(), s)
to_underscored = lambda s: re.sub(r'((?:[a-z]))([A-Z])(?=[a-z]??)', lambda m: m.expand(r'\1_\2'), m).lower()
hexcolor = lambda s: colors.HexColor(str(s))

class barcode_node(General, Inline, Element):
    """
    >>> barcode_node(rawsource='4909411033538')
    <barcode_node: >

    """
    def __init__(self, code_name, options, *children, **attributes):
        self.code_name = code_name
        self.options = options
        Element.__init__(self, '', *children, **attributes)

    def gen_flowable(self, extra_options=None):
        options = dict(self.options)
        if extra_options:
            options.update(
                dict((k, v)
                     for k, v in extra_options.items()
                     if k not in options.keys()))
        return createBarcodeDrawing(self.code_name, **options)


class Barcode(rst.Directive):
    """
    Syntax:

    .. barcode:: EAN13
       :value: 4909411033538
       :width: auto
       :height: auto
       :foo: bar
       ...
    
    """
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = None
    code_name = 'Abstract'

    def build_args(self):
        return str(self.arguments[0])

    def build_options(self):
        opdict = dict((to_camelcase(k), v)
                      for k, v in self.options.items()
                      if v is not None)
        opdict['value'] = self.build_args()
        return opdict

    def run(self):
        # return [barcode_node(self.widget_class, self.build_args(), self.build_options())]
        return [barcode_node(self.code_name, self.build_options())]
    

class EanCode(Barcode):
    """
    EAN code abstract.
    """
    option_spec = dict(
        font_name=str,
        font_size=units.toLength,
        bar_fill_color=hexcolor,
        bar_height=units.toLength,
        bar_width=units.toLength,
        bar_stroke_width=units.toLength,
        bar_stroke_color=hexcolor,
        text_color=hexcolor,
        human_readable=rst.directives.flag,
        quiet=rst.directives.flag,
        lquiet=rst.directives.flag,
        rquiet=rst.directives.flag,
        )
    code_name = 'EAN Abstract'


class Ean13(EanCode):
    """
    Syntax::
      .. ean13:: 4909411033538
          :font_name: Helvetica
          :font_size: 8
          :bar_fill_color: #000000
          :bar_height: 76.2
          :bar_width: 0.33
          :bar_stroke_width: 0.33
          :bar_stroke_color: #000000
          :text_color: #000000
          :human_readable:
          :quiet:
          :lquiet:
          :rquiet:
    """
    code_name = 'EAN13'

rst.directives.register_directive('ean13', Ean13)

    
class Ean8(EanCode):
    """
    Syntax::
      .. ean8:: 12345678
          :font_name: Helvetica
          :font_size: 8
          :bar_fill_color: #000000
          :bar_height: 76.2
          :bar_width: 0.33
          :bar_stroke_width: 0.33
          :bar_stroke_color: #000000
          :text_color: #000000
          :human_readable:
          :quiet:
          :lquiet:
          :rquiet:
    """
    code_name = 'EAN8'

rst.directives.register_directive('ean8', Ean8)

    
class I2of5(Barcode):
    """
    Syntax::
      .. i2of5:: 1234
          :bar_width: float, 0.0075
          :ratio: float, 2.2
          :gap: float, None
          :bar_height: float, (attend)
          :checksum: bool, True
          :bearers: 3.0
          :quiet: bool, True
          :lquiet: float, (attend)
          :rquiet: float, (attend)
          :stop: bool, True
    """
    option_spec = dict(
        ratio=float,
        gap=float,
        bar_width=units.toLength,
        checksum=rst.directives.flag,
        bearers=float,
        quiet=rst.directives.flag,
        lquiet=float,
        rquiet=float,
        stop=rst.directives.flag,
        )
    code_name = 'I2of5'
    
rst.directives.register_directive('i2of5', I2of5)


if __name__=="__main__":
    from doctest import testmod
    testmod()
