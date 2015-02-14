#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
import pkg_resources

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, 2011, 2015 GiMaRIS"
__credits__ = ["Serrano Pereira <serrano.pereira@gmail.com>"]
__license__ = "GPL3"
__version__ = "0.4"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"

def we_are_frozen():
    """Returns True if frozen via py2exe."""
    return hasattr(sys, "frozen")

def module_path():
    """Return nodule path even if we are frozen using py2exe."""
    if we_are_frozen():
        return os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
    return os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))

def resource_filename(resource_name):
	if we_are_frozen():
	    return os.path.join(module_path(), resource_name)
	else:
	    return pkg_resources.resource_filename(__name__, resource_name)
