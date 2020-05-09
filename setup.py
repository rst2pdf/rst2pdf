# -*- coding: utf-8 -*-

import os
import sys

from setuptools import find_packages, setup

version = '0.97'

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description = read('README.rst')

install_requires = [
        'docutils',
        'jinja2',
        'pdfrw',
        'pygments',
        'reportlab',
        'setuptools',
        'six',
        'smartypants',
        ]

try:
    import json
except ImportError:
    install_requires.append('simplejson')

tests_require = ['pyPdf2']
sphinx_require = ['sphinx']
hyphenation_require = ['wordaxe>=1.0']
svgsupport_require = ['svglib']
aafiguresupport_require = ['aafigure>=0.4']
mathsupport_require = ['matplotlib']
rawhtmlsupport_require = ['xhtml2pdf']

setup(
    name="rst2pdf",
    version=version,
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*,!=3.5.*',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    package_dir={'': '.'},
    package_data=dict(rst2pdf=['styles/*.json',
	'styles/*.style',
	'images/*png',
	'images/*jpg',
	'templates/*tmpl'
	]),
    dependency_links=[
    ],
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=dict(
        tests=tests_require,
        sphinx=sphinx_require,
        hyphenation=hyphenation_require,
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
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
	'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
	'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Documentation',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing',
        'Topic :: Utilities',
    ],
    author="rst2pdf maintainers",
    author_email="maintainers@rstpdf.org",
    description="Convert reStructured Text to PDF via ReportLab.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    license="MIT",
    keywords="restructured convert rst pdf docutils pygments reportlab",
    url="https://rst2pdf.org",
    project_urls={
        'Bug Reports': 'https://github.com/rst2pdf/rst2pdf/issues',
        'Source': 'https://github.com/rst2pdf/rst2pdf',
    },
    download_url="https://github.com/rst2pdf/rst2pdf/releases",
    entry_points={'console_scripts': ['rst2pdf = rst2pdf.createpdf:main']},
    test_suite='rst2pdf.tests.test_rst2pdf.test_suite',  # TODO: this needs to be updated
)
