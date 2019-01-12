# -*- coding: utf-8 -*-
#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

import os
import sys

from setuptools import find_packages, setup

version = '0.94'

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

if sys.version_info[0] > 2:
    sys.stderr.write('rst2pdf is python2-only for now.')
    exit(1)

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
    read('CHANGES.rst')
    + '\n' +
   'Download\n'
    '********\n'
    )

install_requires = [
        'setuptools',
        'docutils',
        'reportlab>=2.4',
        'Pygments',
        'pdfrw',
        ]

try:
    import json
except ImportError:
    install_requires.append('simplejson')

tests_require = ['pyPdf2']
sphinx_require = ['sphinx<1.8.0']
hyphenation_require = ['wordaxe>=1.0']
images_require = ['pillow']
pdfimages_require = ['pyPdf2','PythonMagick']
pdfimages2_require = ['pyPdf2','SWFTools']
svgsupport_require = ['svg2rlg']
aafiguresupport_require = ['aafigure>=0.4']
mathsupport_require = ['matplotlib']
rawhtmlsupport_require = ['xhtml2pdf']

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
    extras_require=dict(
        tests=tests_require,
        sphinx=sphinx_require,
        hyphenation=hyphenation_require,
        images=images_require,
        pdfimages=pdfimages_require,
        pdfimages2=pdfimages2_require,
        svgsupport=svgsupport_require,
        aafiguresupport=aafiguresupport_require,
        mathsupport=mathsupport_require,
        rawhtmlsupport=rawhtmlsupport_require,
    ),
    # metadata for upload to PyPI
    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python:: 2',
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
    url="https://rst2pdf.org",
    download_url="https://github.com/rst2pdf/rst2pdf/releases",
    entry_points={'console_scripts': ['rst2pdf = rst2pdf.createpdf:main']},
    test_suite='rst2pdf.tests.test_rst2pdf.test_suite',  # TODO: this needs to be updated
)
