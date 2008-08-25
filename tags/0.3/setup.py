from setuptools import setup, find_packages
setup(
    name = "rst2pdf",
    version = "0.2",
    packages = ["rst2pdf"],
    package_data = {'rst2pdf': ['*/*.ttf','*.json']},
    install_requires = ['docutils','reportlab>=2.1','Pygments'],
    # metadata for upload to PyPI
    author = "Roberto Alsina",
    author_email = "ralsina@netmanagers.com.ar",
    description = "Convert restructured text to PDF via reportlab.",
    license = "MIT",
    keywords = "rst pdf docutils reportlab",
    url = "http://rst2pdf.googlecode.com",   # project home page, if any
    download_url = "http://code.google.com/p/rst2pdf/downloads/list",
    entry_points = {'console_scripts': ['rst2pdf = rst2pdf.rst2pdf:main']},

)
