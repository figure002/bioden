#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2010, 2011, 2015 GiMaRIS <info@gimaris.com>
#
#  This file is part of BioDen - A data normalizer and transponer for
#  files containing taxon biomass/density data for ecotopes.
#
#  BioDen is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  BioDen is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import warnings

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GObject

import bioden.gui

GObject.threads_init()

# The following is a workaround for the executable created with py2exe.
# When warnings are emitted in windows mode (no console available) the
# warning messages can't be correctly output and the application exits
# with an error message. So we filter out warnings to avoid the problem.
if os.name == 'nt':
    warnings.simplefilter('ignore')

def main():
    bioden.gui.MainWindow()
    Gtk.main()
    sys.exit()

if __name__ == '__main__':
    main()
