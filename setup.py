#!/usr/bin/env python

from distutils.core import setup
import py2exe
import glob

setup(
    name = 'bioden',
    description = "A data normalizer and transponer for CSV files containing taxon biomass/density data for ecotopes.",
    version = '0.1',
    scripts=['bioden.pyw'],
    windows = [
        {'script': 'bioden.pyw',
        }
    ],
    options= {
        'py2exe': {
            'includes': 'pango,atk,gobject,gio,cairo,pangocairo',
            'dll_excludes': [],
            },
        'sdist': {
            'formats': 'zip',
        }
    },
    data_files=[('glade', glob.glob('glade/*.*')),
                ('docs', glob.glob('docs/*.*')),
                ('test-data', glob.glob('test-data/*.*')),
                ('.',['COPYING.txt']),
                ('Microsoft.VC90.CRT', glob.glob('Microsoft.VC90.CRT/*.*')),
    ],
)
