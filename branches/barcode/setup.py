# -*- coding: utf-8 -*-
#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$
import os
from setuptools import setup, find_packages

version = '0.9'

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description = (
    read('LICENSE.txt')
    + '\n' +
    'Detailed Documentation\n'
    '**********************\n'
    + '\n' +
    read('README.txt')
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
        'setuptools',
        'docutils',
        'PIL',
        'reportlab>=2.1',
        'Pygments',
        'simplejson'
        ]

tests_require = ['pyPdf',]
hyphenation_require = ['wordaxe',]
svgsupport_require = ['uniconvertor',]
sphinx_require = ['sphinx',]

setup(
    name="rst2pdf",
    version=version,
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    package_data = {'rst2pdf': ['*.json']},
    include_package_data=True,
    # place to find an egg distrib of reportlab 2.1
    dependency_links = [
       #reportlab as egg
       "http://ftp.schooltool.org/schooltool/eggs/3.4",
       #wordaxe
       "http://sourceforge.net/project/platformdownload.php?group_id=105867",
       #PIL as egg
       "http://dist.repoze.org",
       # uniconvertor
       "http://sk1project.org/downloads/uniconvertor/v1.1.3/uniconvertor-1.1.3.tar.gz",
    ],
    install_requires = install_requires,
    tests_require=tests_require,
    extras_require=dict(tests = tests_require,
                        hyphenation = hyphenation_require,
                        svgsupport = svgsupport_require,
                        sphinx = sphinx_require,
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
        'Topic :: Documentation',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing',
        'Topic :: Utilities',
    ],
    author = "Roberto Alsina",
    author_email = "ralsina at netmanagers dot com dot ar",
    description = "Convert restructured text to PDF via reportlab.",
    long_description=long_description,
    license = "MIT",
    keywords = "restructured convert rst pdf docutils pygments reportlab",
    url = "http://rst2pdf.googlecode.com",
    download_url = "http://code.google.com/p/rst2pdf/downloads/list",
    entry_points = {'console_scripts': ['rst2pdf = rst2pdf.createpdf:main']},
    test_suite = 'rst2pdf.tests.test_rst2pdf.test_suite',
)
