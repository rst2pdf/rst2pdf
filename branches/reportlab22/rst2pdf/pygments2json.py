'''Convert a pygments' generated CSS file into a rst2pdf stylesheet.

You can generate a pygments CSS file like this (replace murphy with whatever style you want)::
  
  pygmentize -S murphy -f html
  
'''

import sys,simplejson
from pygments.token import STANDARD_TYPES
dstyles={}
# First create a dumb stylesheet
for key in STANDARD_TYPES:
    dstyles["pygments-"+STANDARD_TYPES[key]]={'parent':'code'}


styles=[]
for line in open(sys.argv[1]):
    line=line.strip()
    sname="pygments-"+line.split(' ')[0][1:]
    style=dstyles.get(sname,{'parent':'code'})
    options=line.split('{')[1].split('}')[0].split(';')
    for option in options:
        option=option.strip()
        option,argument=option.split(':')
        if option=='color':
            style['textColor']=argument.strip()
        if option=='background-color':
            style['backColor']=argument.strip()
            
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
    styles.append([sname,style])
print simplejson.dumps({'styles':styles})
