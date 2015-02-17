#!/usr/bin/env python
import glob, sys, os, site, shutil
from setuptools import setup
from codecs import open

import py2exe

from bioden import __version__

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the relevant file
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# Copy GTK+ files to working directory for py2exe.
site_dir = site.getsitepackages()[1]
include_dll_path = os.path.join(site_dir, "gnome")

gtk_dirs_to_include = [
    'etc',
    'lib\\gtk-3.0',
    'lib\\girepository-1.0',
    'lib\\gio',
    'lib\\gdk-pixbuf-2.0',
    'share\\glib-2.0',
    'share\\fonts',
    'share\\icons',
    'share\\themes\\Default',
    'share\\themes\\HighContrast'
]

gtk_dlls = []
tmp_dlls = []
cdir = os.getcwd()
for dll in os.listdir(include_dll_path):
    if dll.lower().endswith('.dll'):
        gtk_dlls.append(os.path.join(include_dll_path, dll))
        tmp_dlls.append(os.path.join(cdir, dll))

for dll in gtk_dlls:
    shutil.copy(dll, cdir)

setup(
    name = 'bioden',
    version = __version__,
    description = "A data normalizer and transponer for files containing taxon biomass/density data for ecotopes.",
    long_description=long_description,
    author='Serrano Pereira',
    author_email='serrano.pereira@gmail.com',
    license='GPL3',
    url='https://github.com/figure002/bioden',

    windows = [{
        'script': 'bioden/main.py',
        'icon_resources': [
            (1, 'data/icon.ico')
        ],
    }],
    options= {
        'py2exe': {
            'includes' : ['gi'],
            'packages': ['gi'],
            'dll_excludes': ['libgstreamer-1.0-0.dll'],
        },
    },
    data_files=[
        ('docs', glob.glob('docs/*.*')),
        ('.', ['LICENSE.txt']),
    ],
)

dest_dir = os.path.join(cdir, 'dist')
for dll in tmp_dlls:
    shutil.copy(dll, dest_dir)
    os.remove(dll)

for d in gtk_dirs_to_include:
    shutil.copytree(os.path.join(site_dir, "gnome", d), os.path.join(dest_dir, d))
