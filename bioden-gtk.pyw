#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# A GTK+ frontend for bioden.
#
#  Copyright 2010, GiMaRIS <info@gimaris.com>
#
#  This file is part of bioden.
#
#  bioden is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  bioden is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import subprocess
import time
import threading
import webbrowser

try:
    import pygtk
except ImportError:
    sys.exit("This tool requires PyGTK for Python 2.6. "
        "Please install this module and try again.")
pygtk.require('2.0')
import gtk
try:
    import gobject
except ImportError:
    sys.exit("This tool requires PyGObject for Python 2.6. "
        "Please install this module and try again.")

gobject.threads_init()

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, GiMaRIS"
__credits__ = ["Serrano Pereira <serrano.pereira@gmail.com>"]
__license__ = "GPL3"
__version__ = "0.1"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2010/12/12"

class MainWindow(object):
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('main.glade')

        self.window = self.builder.get_object('main_window')
        self.builder.connect_signals(self)

        # Complete some incomplete widgets.
        self.complete_widgets()

    def complete_widgets(self):
        """Complete incomplete widgets. Not everything could be
        set from Glade3."""

        # Create a CSV filter for file choosers.
        self.filefilter_csv = gtk.FileFilter()
        self.filefilter_csv.set_name("Comma Seperated File (*.csv)")
        self.filefilter_csv.add_mime_type("text/csv")
        self.filefilter_csv.add_pattern("*.csv")

        # Add a CSV filter to the file chooser.
        self.chooser_input_file = self.builder.get_object('chooser_input_file')
        self.chooser_input_file.add_filter(self.filefilter_csv)

        # Add items to the 'property' combobox.
        self.liststore_property = gtk.ListStore(gobject.TYPE_STRING)
        self.combobox_property = self.builder.get_object('combobox_property')
        self.combobox_property.set_model(self.liststore_property)
        cell = gtk.CellRendererText()
        self.combobox_property.pack_start(cell, True)
        self.combobox_property.add_attribute(cell, 'text', 0)
        self.combobox_property.append_text('biomass')
        self.combobox_property.append_text('density')
        self.combobox_property.set_active(0)

        # Set the default value for the 'round' spinbutton.
        self.builder.get_object('adjustment_round').set_value(-1)

    def on_window_destroy(self, widget, data=None):
        gtk.main_quit()

    def on_button_start_clicked(self, widget, data=None):
        # Get some values from the GUI.
        input_file = self.chooser_input_file.get_filename()
        output_folder = self.builder.get_object('chooser_output_folder').get_filename()

        # Check if the input file and output folder are set.
        if not input_file:
            self.show_message(title="No data file set",
                message="You didn't select the data file. Please select the data file first.",
                type=gtk.MESSAGE_ERROR)
            return

        if not output_folder:
            self.show_message(title="No output folder set",
                message="You didn't select the output folder. Please select the output folder first.",
                type=gtk.MESSAGE_ERROR)
            return

        # Get all values from the GUI.
        delimiter = self.builder.get_object('input_delimiter').get_text()
        quotechar = self.builder.get_object('input_quotechar').get_text()
        active = self.combobox_property.get_active()
        property = self.liststore_property[active][0]
        round_to = "%d" % self.builder.get_object('spinbutton_round').get_value()

        # Construct the command to be executed.
        bioden_exe = os.path.join('./','bioden.py')
        args = [sys.executable, bioden_exe, '-i', input_file, '-o', output_folder,
            '-d', delimiter, '-q', quotechar, '-p', property]

        # Set the argument 'round' if 'round_to' set to 0 or higher.
        if int(round_to) >= 0:
            args.extend(['-r', round_to])

        # Check if the bioden tool is present.
        if not os.path.isfile(bioden_exe):
            raise EnvironmentError("Cannot locate file '%s'." % args[1])

        # Show the progress dialog.
        self.pd = self.builder.get_object('progress_dialog').show()

        # Start the bioden process.
        t = StartProcess(args)
        t.start()

        # Run an updater thread that controls the progress dialog.
        t2 = Updater(t, self.builder)
        t2.start()

    def show_message(self, title, message, type=gtk.MESSAGE_INFO):
        """Show a message dialog showing that input file was not set."""
        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=type,
            buttons=gtk.BUTTONS_OK,
            message_format=title)
        dialog.format_secondary_text(message)

        response = dialog.run()
        dialog.destroy()

    def on_about(self, widget, data=None):
        about = self.builder.get_object('about_dialog')
        about.set_version(__version__)
        about.run()
        about.hide()

    def on_help(button, section):
        """Display the help contents in the system's default web
        browser.
        """

        # Construct the path to the help file.
        path = os.path.abspath('./docs/user-manual.html')

        # Turn the path into an URL.
        if path.startswith('/'):
            url = 'file://'+path
        else:
            url = 'file:///'+path

        # Open the URL in the system's web browser.
        webbrowser.open(url)

    def on_fin_button_ok_clicked(self, widget, data=None):
        self.builder.get_object('message_finished').hide()

    def on_err_button_ok_clicked(self, widget, data=None):
        self.builder.get_object('message_error').hide()

class StartProcess(threading.Thread):
    def __init__(self, args):
        super(StartProcess, self).__init__()
        self.args = args
        self.p = None
        self.tries = 0

    def get_poll(self):
        if self.tries >= 3:
            return -100

        if self.p:
            return self.p.poll()
        else:
            self.tries += 1
            time.sleep(0.5)
            return

    def run(self):
        self.p = subprocess.Popen(self.args, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

class Updater(threading.Thread):
    def __init__(self, proc, builder):
        super(Updater, self).__init__()
        self.proc = proc
        self.builder = builder

    def run(self):
        progress_dialog = self.builder.get_object('progress_dialog')
        progress_bar = self.builder.get_object('pd_progressbar')

        # Check if the process was terminated. If get_poll() returns
        # None, the progress is still running.
        while self.proc.get_poll() == None:
            # Update the progress bar.
            gobject.idle_add(progress_bar.pulse)
            time.sleep(0.1)

        # The process has finished. Hide the progress dialog. We don't
        # destroy it, because the builder doesn't seem capable of
        # creating a new instance.
        gobject.idle_add(progress_dialog.hide)

        # Get the value of the return code.
        returncode = self.proc.get_poll()

        if returncode == 0:
            # Show a message dialog showing that the process was finished.
            message_finished = self.builder.get_object('message_finished')
            output_folder = self.builder.get_object('chooser_output_folder').get_filename()

            gobject.idle_add(message_finished.format_secondary_text,
                "The data was successfully processed. The output files "
                "have been saved to %s" % output_folder)
            gobject.idle_add(message_finished.run)
        elif returncode == -100:
            # Show a error dialog showing that something went wrong.
            message_error = self.builder.get_object('message_error')
            gobject.idle_add(message_error.format_secondary_text,
                "An unknown error has occurred. Please contact the "
                "programmer about this problem.")
            gobject.idle_add(message_error.run)
        else:
            # Show a error dialog showing that something went wrong.
            message_error = self.builder.get_object('message_error')
            #errormsg = self.proc.p.stderr.readlines()
            gobject.idle_add(message_error.format_secondary_text,
                "This is probably caused by an incorrect input file or "
                "the input file is in a different format. If the input file is in a "
                "different CSV format, change the settings accordingly "
                "under Advanced Options.")
            gobject.idle_add(message_error.run)

if __name__ == '__main__':
    app = MainWindow()
    gtk.main()
    sys.exit(0)
