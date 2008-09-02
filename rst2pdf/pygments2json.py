'''Convert a pygments' generated CSS file into a rst2pdf stylesheet.

You can generate a pygments CSS file like this (replace murphy with whatever style you want)::
  
  pygmentize -S murphy -f html
  
'''

import sys,simplejson

styles={}
for line in open(sys.argv[1]):
    style={}
    line=line.strip()
    sname="pygments-"+line.split(' ')[0][1:]
    options=line.split('{')[1].split('}')[0].split(';')
    for option in options:
        option=option.strip()
        option,argument=option.split(':')
        if option=='color':
            style['textColor']=argument
        if option=='background-color':
            style['backColor']=argument
            
        # These two can come in any order
        if option=='font-weight' and argument=='bold':
            if 'fontName' in style and style['fontName']=='stdMonoItalic':
              style['fontName']='stdMonoBoldItalic'
            else:
              style['fontName']='stdMonoBold'
        if option=='font-style' and argument=='italic':
            if 'fontName' in style and style['fontName']=='stdBold':
              style['fontName']='stdMonoBoldItalic'
            else:
              style['fontName']='stdMonoItalic'
    styles[sname]=style
print simplejson.dumps({'styles':styles})
