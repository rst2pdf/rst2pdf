# -*- coding: utf-8 -*-
#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

import os
from setuptools import setup, find_packages

version = '0.93'

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description = (
    read('LICENSE.txt')
    + '\n' +
    'Detailed Documentation\n'
    '**********************\n'
    + '\n' +
    read('README.rst')
    + '\n' +
    'Contributors\n'
    '************\n'


    + '\n' +
    read('Contributors.txt')
    + '\n' +
    'Change history\n'
    '**************\n'
    + '\n' +
    read('CHANGES.txt')
    + '\n' +
   'Download\n'
    '********\n'
    )

install_requires = [
    'setuptools>=18.5',
    'docutils',
    'reportlab>=2.4',
    'Pygments',
    'pdfrw',
    'future',
    'Jinja2'
]

try:
    import json
except ImportError:
    install_requires.append('simplejson')

tests_require = ['pyPdf', 'nose', 'coverage']

EXTRAS_REQUIRE = {
    'tests': tests_require,
    'sphinx': ['sphinx'],
    'hyphenation': ['wordaxe>=1.0', 'pyhyphen'],
    'images': ['pillow'],
    'pdfimages': ['pyPdf'], # , 'PythonMagick'],
    'pdfimages2': ['pyPdf'], # , 'SWFTools'],
    'svgsupport': ['svg2rlg'],
    'aafiguresupport': ['aafigure>=0.4'],
    'mathsupport': ['matplotlib'],
    'rawhtmlsupport': ['xhtml2pdf']
}

setup(
    name="rst2pdf",
    version=version,
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    package_data=dict(rst2pdf=['styles/*.json',
	'styles/*.style',
	'images/*png',
	'images/*jpg',
	'templates/*tmpl'
	]),
    include_package_data=True,
    dependency_links=[
    ],
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=EXTRAS_REQUIRE,
    # metadata for upload to PyPI
    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Documentation',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing',
        'Topic :: Utilities',
    ],
    author="Roberto Alsina",
    author_email="ralsina at netmanagers dot com dot ar",
    description="Convert restructured text to PDF via reportlab.",
    long_description=long_description,
    license="MIT",
    keywords="restructured convert rst pdf docutils pygments reportlab",
    url="http://rst2pdf.ralsina.me/stories/index.html",
    download_url="https://github.com/rst2pdf/rst2pdf/releases",
    entry_points={'console_scripts': ['rst2pdf = rst2pdf.createpdf:main']},
    test_suite='rst2pdf.tests.test_rst2pdf.test_suite',  # TODO: this needs to be updated
)
