#!/usr/bin/env python

import glob

#from distutils.core import setup
from setuptools import setup
import py2exe

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

    windows = [
        {'script': 'bioden.pyw',
        'icon_resources': [(1, '../data/icon.ico')],
        }
    ],
    options= {
        'py2exe': {
            'includes': 'pango,atk,gobject,gio,cairo,pangocairo',
            'dll_excludes': [],
            },
    },
    data_files=[('glade', glob.glob('glade/*.*')),
        ('docs', glob.glob('docs/*.*')),
        ('.',['COPYING']),
        ],
)
