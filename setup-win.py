#!/usr/bin/env python
import glob
from setuptools import setup
from codecs import open
from os import path

import py2exe

from bioden import __version__

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name = 'bioden',
    version = __version__,
    description = "A data normalizer and transponer for files containing taxon biomass/density data for ecotopes.",
    long_description=long_description,
    author='Serrano Pereira',
    author_email='serrano.pereira@gmail.com',
    license='GPL3',
    url='http://www.gimaris.com/',

    windows = [{
        'script': 'bioden/main.py',
        'icon_resources': [
            (1, 'data/icon.ico')
        ],
    }],
    options= {
        'py2exe': {
            'includes': 'pango,atk,gobject,gio,cairo,pangocairo',
            'dll_excludes': [],
        },
    },
    data_files=[
        ('docs', glob.glob('docs/*.*')),
        ('.', ['LICENSE.txt']),
    ],
)
