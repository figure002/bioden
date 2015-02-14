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
import threading
import webbrowser
import csv

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GObject

from bioden import __copyright__, __version__, resource_filename
import bioden.std
import bioden.processor

class ProgressDialog:
    """Display a progress dialog."""

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file( resource_filename('glade/pdialog.glade') )

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
        self.builder = Gtk.Builder()
        self.builder.add_from_file( resource_filename('glade/main.glade') )

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
        self.filefilter_csv = Gtk.FileFilter()
        self.filefilter_csv.set_name("Comma Separated Values (.csv)")
        self.filefilter_csv.add_mime_type("text/csv")
        self.filefilter_csv.add_pattern("*.csv")

        # Create a XML filter for file choosers.
        self.filefilter_xsl = Gtk.FileFilter()
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

        self.combobox_property = self.builder.get_object('combobox_property')
        self.combobox_output_format = self.builder.get_object('combobox_output_format')

        # Set the default value for the 'round' spinbutton.
        self.builder.get_object('adjustment_round').set_value(-1)

        # Change the background color of the warning frame.
        if os.name == 'posix':
            frame_warning = self.builder.get_object('frame_warning')
            frame_warning.set_shadow_type(Gtk.ShadowType.OUT)
            #color = Gdk.color_parse('#EFE0CD')
            #frame_warning.modify_bg(Gtk.StateType.NORMAL, color)

    def on_combobox_output_format_changed(self, combobox, data=None):
        """Show the .xls warning message if the user selected .xls as the
        output format.
        """
        active = combobox.get_active()
        output_format = self.combobox_output_format.get_active_text()
        if ".xls" in output_format:
            self.builder.get_object('frame_warning').show()
        else:
            self.builder.get_object('frame_warning').hide()

    def on_window_destroy(self, widget, data=None):
        Gtk.main_quit()

    def on_button_start_clicked(self, widget, data=None):
        # Get some values from the GUI.
        input_file = self.chooser_input_file.get_filename()
        output_folder = self.builder.get_object('chooser_output_folder').get_filename()

        # Check if the input file and output folder are set.
        if not input_file:
            self.show_message(title="No data file selected",
                message="You didn't select the data file. Please select the data file first.",
                type=Gtk.MessageType.ERROR)
            return

        # Get all values from the GUI.
        delimiter = self.builder.get_object('entry_delimiter').get_text()
        quotechar = self.builder.get_object('entry_quotechar').get_text()
        active = self.combobox_property.get_active()
        prop = self.combobox_property.get_active_text()
        active = self.combobox_output_format.get_active()
        output_format = self.combobox_output_format.get_active_text()
        target_sample_surface = float(self.builder.get_object('entry_sample_surface').get_text())
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
            t.set_csv_dialect(delimiter, quotechar)
            t.set_input_file(input_file, 'csv')
        elif ".xls" in self.filter_name:
            t = bioden.processor.XLSProcessor()
            t.set_input_file(input_file, 'xls')
        t.set_property(prop)
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

    def on_load_data_failed(self, sender, strerror, data=None):
        """Show a error dialog showing that loading the data has failed."""

        # Close the progress dialog.
        self.pd.dialog.destroy()

        # Build an error dialog.
        builder = Gtk.Builder()
        builder.add_from_file( resource_filename('glade/errdialog.glade') )

        dialog = builder.get_object('error_dialog')
        textbuffer = builder.get_object('textbuffer_details')

        if ".csv" in self.filter_name:
            message = ("The data could not be loaded. This is probably caused by "
                "an incorrect input file or the CSV file was in a different "
                "format. If the CSV file was in a different format, "
                "change the settings under \"CSV Input File Options\" accrodingly "
                "and make sure the format matches the format described in the "
                "documentation.")
        elif ".xls" in self.filter_name:
            message = ("The data could not be loaded. This is probably caused by "
                "an incorrect input file or the XLS file was in a different "
                "format. Make sure the format matches the format described in "
                "the documentation.")

        dialog.format_secondary_text(message)
        textbuffer.set_text(strerror)
        dialog.run()
        dialog.destroy()

    def show_message(self, title, message, type=Gtk.MessageType.INFO):
        """Show a message dialog showing that input file was not set."""
        dialog = Gtk.MessageDialog(parent=None, flags=0,
            type=type,
            buttons=Gtk.ButtonsType.OK,
            message_format=title)
        dialog.format_secondary_text(message)
        dialog.set_position(Gtk.WindowPosition.CENTER)
        dialog.run()
        dialog.destroy()

    def on_about(self, widget, data=None):
        about = self.builder.get_object('about_dialog')
        about.set_copyright(__copyright__)
        about.set_version(__version__)
        about.run()
        about.hide()

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
