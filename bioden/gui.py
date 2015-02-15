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

class ProgressDialog(object):
    """Display a progress dialog."""

    def __init__(self, parent=None, worker=None):
        self.worker = None
        self.builder = Gtk.Builder()
        self.builder.add_from_file( resource_filename('glade/progress_dialog.glade') )
        self.dialog = self.builder.get_object('progress_dialog')
        self.dialog.set_transient_for(parent)
        self.progress_bar = self.builder.get_object('progress_bar')
        self.label_action = self.builder.get_object('label_action')
        self.textview = self.builder.get_object('textview_details')
        self.textbuffer = self.builder.get_object('textbuffer_details')
        self.builder.connect_signals(self)
        self.dialog.show()

    def set_worker(self, worker):
        self.worker = worker

    def destroy(self):
        self.dialog.destroy()

class MainWindow(object):
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file( resource_filename('glade/main.glade') )
        self.window = self.builder.get_object('main_window')
        self.combobox_property = self.builder.get_object('combobox_property')
        self.combobox_output_format = self.builder.get_object('combobox_output_format')

        # Connect the window signals to the handlers.
        self.builder.connect_signals(self)

        # Reset the widgets.
        self.reset_widgets()

        # Set additional signal handlers.
        self.handlers = {
            'process-finished': bioden.std.sender.connect('process-finished',
                self.on_process_finished),
            'load-data-failed': bioden.std.sender.connect('load-data-failed',
                self.on_load_data_failed)
        }

    def reset_widgets(self):
        """Reset the UI components."""
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

        # Set the default value for the 'round' spinbutton.
        self.builder.get_object('adjustment_round').set_value(-1)

    def on_combobox_output_format_changed(self, combobox, data=None):
        """Show/hide the Excel limitation message."""
        active = combobox.get_active()
        output_format = self.combobox_output_format.get_active_text()
        if ".xls" in output_format:
            self.builder.get_object('frame_warning').show()
        else:
            self.builder.get_object('frame_warning').hide()

    def on_window_destroy(self, widget, data=None):
        """Close the application."""
        Gtk.main_quit()

    def on_progress_dialog_destroy(self, widget, data=None):
        """Stop the worker and close the progress dialog."""
        try:
            self.worker.stop()
            self.worker.join()
        except:
            pass
        widget.destroy()

    def on_button_start_clicked(self, widget, data=None):
        """Start processing the data."""
        input_file = self.chooser_input_file.get_filename()
        output_folder = self.builder.get_object('chooser_output_folder').get_filename()
        if not input_file:
            self.show_message(title="No data file selected",
                message="Please select the input file.",
                type=Gtk.MessageType.ERROR)
            return

        # Get all values from the GUI.
        delimiter = self.builder.get_object('entry_delimiter').get_text()
        quotechar = self.builder.get_object('entry_quotechar').get_text()
        active = self.combobox_property.get_active()
        property_ = self.combobox_property.get_active_text()
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
        self.progress_dialog = ProgressDialog(parent=self.window)

        # Set up the data processor.
        if ".csv" in self.filter_name:
            self.worker = bioden.processor.CSVProcessor()
            self.worker.set_csv_dialect(delimiter, quotechar)
            self.worker.set_input_file(input_file, 'csv')
        elif ".xls" in self.filter_name:
            self.worker = bioden.processor.XLSProcessor()
            self.worker.set_input_file(input_file, 'xls')
        self.worker.set_property(property_)
        self.worker.set_output_folder(output_folder)
        self.worker.set_progress_dialog(self.progress_dialog)
        self.worker.set_target_sample_surface(target_sample_surface)
        self.worker.set_output_format(output_format)
        if decimals >= 0:
            self.worker.set_round(decimals)

        self.progress_dialog.set_worker(self.worker)

        # Start processing the data.
        self.worker.start()

    def on_process_finished(self, sender):
        """Show a message dialog showing that the process was finished."""
        output_folder = self.builder.get_object('chooser_output_folder').get_filename()

        message_finished = self.show_message("Finished!",
            "The output files have been saved to\n%s." % output_folder)

    def on_load_data_failed(self, sender, strerror, data=None):
        """Show a error dialog showing that loading the data has failed."""
        self.progress_dialog.dialog.destroy()

        # Build an error dialog.
        builder = Gtk.Builder()
        builder.add_from_file( resource_filename('glade/error_dialog.glade') )

        dialog = builder.get_object('error_dialog')
        dialog.set_transient_for(self.window)

        if ".csv" in self.filter_name:
            message = ("The data could not be loaded. This is probably caused "
                "by an incorrect input file or the CSV file was in a different "
                "format. If the CSV file was in a different format, change "
                "the settings under \"CSV Input File Options\" accordingly "
                "and make sure the format matches the format described in the "
                "documentation.")
        elif ".xls" in self.filter_name:
            message = ("The data could not be loaded. This is probably caused "
                "by an incorrect input file or the XLS file was in a different "
                "format. Make sure the format matches the format described in "
                "the documentation.")

        dialog.format_secondary_text(message)
        textbuffer = builder.get_object('textbuffer_details')
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
        dialog.set_transient_for(self.window)
        dialog.run()
        dialog.destroy()

    def on_about(self, widget, data=None):
        """Display the about dialog."""
        about = self.builder.get_object('about_dialog')
        about.set_copyright(__copyright__)
        about.set_version(__version__)
        about.run()
        about.hide()

    def on_help(button, section):
        """Display the help contents in the web browser."""
        path = os.path.abspath(os.path.join('.','docs','index.html'))
        if path.startswith('/'):
            url = "file://{0}".format(path)
        else:
            url = "file:///{0}".format(path)
        webbrowser.open(url)
