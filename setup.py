#!/usr/bin/env python

from distutils.core import setup
import py2exe
import glob

opts = {
    "py2exe": {
        "includes": "pango,atk,gobject,gio,cairo,pangocairo",
        "dll_excludes": [
        "iconv.dll","intl.dll","libatk-1.0-0.dll",
        "libgdk_pixbuf-2.0-0.dll","libgdk-win32-2.0-0.dll",
        "libglib-2.0-0.dll","libgmodule-2.0-0.dll",
        "libgobject-2.0-0.dll","libgthread-2.0-0.dll",
        "libgtk-win32-2.0-0.dll","libpango-1.0-0.dll",
        "libpangowin32-1.0-0.dll"],
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
                ("docs", glob.glob("docs/*.*"))
    ],
)
