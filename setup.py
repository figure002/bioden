#!/usr/bin/env python

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
    url='https://sourceforge.net/p/bioden/home/',
    keywords = 'gimaris ecotope biomass density ambi',
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
        'pygtk',
        'pygobject',
        'pycairo',
        'xlrd',
        'xlwt',
        ],
)
