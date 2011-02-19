#!/usr/bin/env python

import glob

#from distutils.core import setup
from setuptools import setup

setup(
    name = 'bioden',
    version = '0.3',
    description = "A data normalizer and transponer for files containing taxon biomass/density data for ecotopes.",
    long_description="A data normalizer and transponer for files containing taxon biomass/density data for ecotopes.",
    author='Serrano Pereira',
    author_email='serrano.pereira@gmail.com',
    license='GPL3',
    platforms=['GNU/Linux','Windows'],
    url='http://www.gimaris.com/',
    keywords = 'gimaris invasive species settlement setl analysis',
    classifiers = [
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Natural Language :: English",
    ],
    install_requires = [
        'setuptools',
        'pygtk >= 2.22',
        'pygobject >= 2.26',
        'pycairo >= 1.8.6',
        'xlrd',
        'xlwt',
        ],

    """
    scripts=['bioden.pyw'],
    packages = ['bioden'],
    data_files=[
        ('glade', glob.glob('glade/*.*')),
        ('docs', glob.glob('docs/*.*')),
        ('.',['COPYING','INSTALL','README']),
        ],
    """
)
