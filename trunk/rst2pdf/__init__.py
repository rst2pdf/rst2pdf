__import__('pkg_resources').declare_namespace(__name__)

VERSION = (0, 9, 0, 'svn')

def version():
    return '%s.%s.%s-%s' % VERSION
