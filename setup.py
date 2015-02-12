#!/usr/bin/env python
from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='bioden',
    version='0.3',
    description='A data normalizer and transponer for files containing taxon biomass/density data for ecotopes.',
    long_description=long_description,
    url='https://sourceforge.net/p/bioden/home/',
    author='Serrano Pereira',
    author_email='serrano.pereira@gmail.com',
    license='GPL3',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Natural Language :: English",
    ],
    keywords = 'gimaris ecotope biomass density ambi',
    packages=find_packages(exclude=['docs']),
    install_requires=[
        'xlrd',
        'xlwt',
    ],
    package_data={
        'bioden': [
            'glade/about.glade',
            'glade/errdialog.glade',
            'glade/main.glade',
            'glade/main_win7.glade',
            'glade/pdialog.glade',
        ]
    },
    entry_points={
        'gui_scripts': [
            'bioden = bioden.main:main',
        ]
    }
)
