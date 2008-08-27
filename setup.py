# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description = (
    read('README.txt')
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
        'reportlab>=2.1',
        'Pygments',
        'simplejson',
        ]
        
tests_require = install_requires
    
setup(
    name = "rst2pdf",
    version = "0.5",
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    package_data = {'rst2pdf': ['*/*.ttf','*.json']},
    namespace_packages=['rst2pdf'],
    include_package_data=True,
    # place to find an egg distrib of reportlab 2.1
    dependency_links = [
       "http://ftp.schooltool.org/schooltool/eggs/3.4"
    ], 
    install_requires = install_requires,
    tests_require=tests_require,
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
    entry_points = {'console_scripts': ['rst2pdf = rst2pdf.rst2pdf:main']},
    test_suite = 'rst2pdf.tests.test_rst2pdf.test_suite',
)
