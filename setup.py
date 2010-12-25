#!/usr/bin/env python

from distutils.core import setup
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
    data_files=[('glade', glob.glob('glade/*.*')),
        ('docs', glob.glob('docs/*.*')),
        ('test-data', glob.glob('test-data/*.*')),
        ('.',['COPYING']),
        ],
)
