#!/usr/bin/env python

from distutils.core import setup
import py2exe
import glob

setup(
    name = 'bioden',
    version = '0.2',
    description = "A data normalizer and transponer for CSV files containing taxon biomass/density data for ecotopes.",
    long_description="A data normalizer and transponer for CSV files containing taxon biomass/density data for ecotopes.",
    author='Serrano Pereira',
    author_email='serrano.pereira@gmail.com',
    license='GPL3',
    platforms=['GNU/Linux','Windows'],
    url='http://www.gimaris.com/',

    scripts=['bioden.pyw'],
    windows = [
        {'script': 'bioden.pyw',
        'icon_resources': [(1, 'icon.ico')],
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
                ('test-data', glob.glob('test-data/*.*')),
                ('.',['COPYING.txt']),
                ('.',['icon.ico']),
                ('Microsoft.VC90.CRT', glob.glob('Microsoft.VC90.CRT/*.*')),
    ],
)
