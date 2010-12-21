#!/usr/bin/env python

from distutils.core import setup
import py2exe
import glob

opts = {
    "py2exe": {
        "includes": "pango,atk,gobject,gio,cairo,pangocairo",
        "dll_excludes": [],
        }
    }

setup(
    name = "bioden",
    description = "A data normalizer and transponer for CSV files containing taxon biomass/density data for ecotopes.",
    version = "0.1",
    windows = [
        {"script": "bioden.pyw",
        }
    ],
    options=opts,
    data_files=[("glade", glob.glob("glade/*.*")),
                ("docs", glob.glob("docs/*.*")),
                ("test-data", glob.glob("test-data/*.*")),
                ('.',['COPYING.txt']),
    ],
)
