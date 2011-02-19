#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2010, 2011, GiMaRIS <info@gimaris.com>
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
import threading
import webbrowser
import csv

import pygtk
pygtk.require('2.0')
import gtk
import gobject

import bioden.std
import bioden.processor

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__credits__ = ["Serrano Pereira <serrano.pereira@gmail.com>"]
__license__ = "GPL3"
__version__ = "0.3"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2011/02/18"


class ProgressDialog:
    """Display a progress dialog."""

    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('glade/pdialog.glade')

        self.dialog = self.builder.get_object('progress_dialog')
        self.pbar = self.builder.get_object('progressbar')
        self.label_action = self.builder.get_object('label_action')
        self.textview = self.builder.get_object('textview_details')
        self.textbuffer = self.builder.get_object('textbuffer_details')

        self.dialog.show()

    def destroy(self):
        self.dialog.destroy()

class MainWindow:
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('glade/main.glade')

        self.window = self.builder.get_object('main_window')

        # Connect the window signals to the handlers.
        self.builder.connect_signals(self)

        # Complete some incomplete widgets.
        self.complete_widgets()

        # Handle application signals.
        self.handler1 = bioden.std.sender.connect('process-finished',
            self.on_process_finished)
        self.handler2 = bioden.std.sender.connect('load-data-failed',
            self.on_load_data_failed)

    def complete_widgets(self):
        """Complete incomplete widgets. These are the things I couldn't
        set from Glade 3."""

        # Create a CSV filter for file choosers.
        self.filefilter_csv = gtk.FileFilter()
        self.filefilter_csv.set_name("Comma Separated Values (.csv)")
        self.filefilter_csv.add_mime_type("text/csv")
        self.filefilter_csv.add_pattern("*.csv")

        # Create a XML filter for file choosers.
        self.filefilter_xsl = gtk.FileFilter()
        self.filefilter_xsl.set_name("Microsoft Excel 97/2000/XP (.xls)")
        self.filefilter_xsl.add_mime_type("application/vnd.ms-excel")
        self.filefilter_xsl.add_pattern("*.xls")

        # Add filters to the file chooser.
        self.chooser_input_file = self.builder.get_object('chooser_input_file')
        self.chooser_input_file.add_filter(self.filefilter_xsl)
        self.chooser_input_file.add_filter(self.filefilter_csv)

        # Set the default folder for the output folder to the user's
        # home folder rather than bioden's installation folder.
        chooser_output_folder = self.builder.get_object('chooser_output_folder')
        chooser_output_folder.set_current_folder(os.path.expanduser('~'))

        # Add items to the 'property' combobox.
        #print gobject.type_name(gobject.TYPE_STRING)
        self.combobox_property = self.builder.get_object('combobox_property')
        cell = gtk.CellRendererText()
        self.combobox_property.pack_start(cell, True)
        self.combobox_property.add_attribute(cell, 'text', 0)
        self.combobox_property.append_text('biomass')
        self.combobox_property.append_text('density')
        self.combobox_property.set_active(0)

        # Add items to the 'output format' combobox.
        #print gobject.type_name(gobject.TYPE_STRING)
        self.combobox_output_format = self.builder.get_object('combobox_output_format')
        cell = gtk.CellRendererText()
        self.combobox_output_format.pack_start(cell, True)
        self.combobox_output_format.add_attribute(cell, 'text', 0)
        self.combobox_output_format.append_text("Comma Separated Values (.csv)")
        self.combobox_output_format.append_text("Microsoft Excel 97/2000/XP (.xls)")
        self.combobox_output_format.set_active(0)

        # Set the default value for the 'round' spinbutton.
        self.builder.get_object('adjustment_round').set_value(-1)

        # Change the background color of the warning frame.
        if os.name == 'posix':
            frame_warning = self.builder.get_object('frame_warning')
            frame_warning.set_shadow_type(gtk.SHADOW_OUT)
            #color = gtk.gdk.color_parse('#EFE0CD')
            #frame_warning.modify_bg(gtk.STATE_NORMAL, color)

    def on_combobox_output_format_changed(self, combobox, data=None):
        """Show the .xls warning message if the user selected .xls as the
        output format.
        """
        active = combobox.get_active()
        output_format = self.builder.get_object('liststore_output_format')[active][0]
        if ".xls" in output_format:
            self.builder.get_object('frame_warning').show()
        else:
            self.builder.get_object('frame_warning').hide()

    def on_window_destroy(self, widget, data=None):
        gtk.main_quit()

    def on_button_start_clicked(self, widget, data=None):
        # Get some values from the GUI.
        input_file = self.chooser_input_file.get_filename()
        output_folder = self.builder.get_object('chooser_output_folder').get_filename()

        # Check if the input file and output folder are set.
        if not input_file:
            self.show_message(title="No data file selected",
                message="You didn't select the data file. Please select the data file first.",
                type=gtk.MESSAGE_ERROR)
            return

        # Get all values from the GUI.
        delimiter = self.builder.get_object('input_delimiter').get_text()
        quotechar = self.builder.get_object('input_quotechar').get_text()
        active = self.combobox_property.get_active()
        property = self.builder.get_object('liststore_property')[active][0]
        active = self.combobox_output_format.get_active()
        output_format = self.builder.get_object('liststore_output_format')[active][0]
        target_sample_surface = float(self.builder.get_object('input_sample_surface').get_text())
        decimals = int(self.builder.get_object('spinbutton_round').get_value())

        # Normalize the output format name.
        if '.csv' in output_format:
            output_format = 'csv'
        elif '.xls' in output_format:
            output_format = 'xls'

        # Get the name of the selected file type.
        self.filter_name = self.builder.get_object('chooser_input_file').get_filter().get_name()

        # Show the progress dialog.
        self.pd = ProgressDialog()

        # Set up the data processor.
        if ".csv" in self.filter_name:
            t = bioden.processor.CSVProcessor()
            t.set_input_file(input_file, 'csv')
        elif ".xls" in self.filter_name:
            t = bioden.processor.XLSProcessor()
            t.set_input_file(input_file, 'xls')
        t.set_property(property)
        t.set_output_folder(output_folder)
        t.set_progress_dialog(self.pd)
        t.set_target_sample_surface(target_sample_surface)
        t.set_output_format(output_format)
        if decimals >= 0:
            t.set_round(decimals)

        # Start processing the data.
        t.start()

    def on_process_finished(self, sender):
        """Show a message dialog showing that the process was finished."""
        output_folder = self.builder.get_object('chooser_output_folder').get_filename()

        message_finished = self.show_message("Finished!",
            "The data was successfully processed. The output files "
            "have been saved to '%s'." % output_folder)

    def on_load_data_failed(self, sender):
        """Show a error dialog showing that loading the data has failed."""

        # Close the progress dialog.
        self.pd.dialog.destroy()

        if ".csv" in self.filter_name:
            self.show_message("Loading data failed!",
                "The data could not be loaded. This is probably caused by "
                "an incorrect input file or the CSV file was in a different "
                "format. If the CSV file was in a different format, "
                "change the settings under \"CSV Input File Options\" accrodingly "
                "and make sure the format matches the format described in the "
                "documentation.",
                type=gtk.MESSAGE_ERROR)
        elif ".xls" in self.filter_name:
            self.show_message("Loading data failed!",
                "The data could not be loaded. This is probably caused by "
                "an incorrect input file or the XLS file was in a different "
                "format. Make sure the format matches the format described in "
                "the documentation.",
                type=gtk.MESSAGE_ERROR)

    def show_message(self, title, message, type=gtk.MESSAGE_INFO):
        """Show a message dialog showing that input file was not set."""
        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=type,
            buttons=gtk.BUTTONS_OK,
            message_format=title)
        dialog.format_secondary_text(message)
        dialog.set_position(gtk.WIN_POS_CENTER)
        dialog.run()
        dialog.destroy()

    def on_about(self, widget, data=None):
        builder = gtk.Builder()
        builder.add_from_file('glade/about.glade')

        about = builder.get_object('about_dialog')
        about.set_copyright(__copyright__)
        about.set_version(__version__)
        about.run()
        about.destroy()

    def on_help(button, section):
        """Display the help contents in the system's default web
        browser.
        """

        # Construct the path to the help file.
        path = os.path.abspath(os.path.join('.','docs','documentation.html'))

        # Turn the path into an URL.
        if path.startswith('/'):
            url = 'file://'+path
        else:
            url = 'file:///'+path

        # Open the URL in the system's web browser.
        webbrowser.open(url)
