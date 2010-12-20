#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# bioden - description here...
#
#  Copyright 2010, GiMaRIS <info@gimaris.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import time
import threading
import webbrowser
import csv
import logging
from sqlite3 import dbapi2 as sqlite

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


def to_float(x):
    """Return the float from a number which uses a comma as the decimal
    separator."""
    return float(x.replace(',','.'))

def uniqify(seq):
    """Remove all duplicates from a list."""
    return {}.fromkeys(seq).keys()

def median(values):
    """Return the median of a series of numbers."""
    values = sorted(values)
    count = len(values)

    if count % 2 == 1:
        return values[(count+1)/2-1]
    else:
        lower = values[count/2-1]
        upper = values[count/2]
        return (float(lower + upper)) / 2


class Sender(gobject.GObject):
    """Custom GObject for emitting custom signals."""
    __gsignals__ = {
        'process-finished': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'load-data-failed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
    }

    def __init__(self):
        gobject.GObject.__init__(self)

class ProgressDialog(object):
    """Display a progress dialog."""

    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('glade/pdialog.glade')

        self.dialog = self.builder.get_object('progress_dialog')
        self.pbar = self.builder.get_object('progressbar')
        self.label_action = self.builder.get_object('label_action')

        self.dialog.show()

class MainWindow(object):
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('glade/main.glade')

        self.window = self.builder.get_object('main_window')
        self.builder.connect_signals(self)

        # Complete some incomplete widgets.
        self.complete_widgets()

        # Handle application signals.
        self.handler1 = sender.connect('process-finished',
            self.on_process_finished)
        self.handler2 = sender.connect('load-data-failed',
            self.on_load_data_failed)

    def complete_widgets(self):
        """Complete incomplete widgets. These are the things I couldn't
        set from Glade 3."""

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

        # Get all values from the GUI.
        delimiter = self.builder.get_object('input_delimiter').get_text()
        quotechar = self.builder.get_object('input_quotechar').get_text()
        active = self.combobox_property.get_active()
        property = self.liststore_property[active][0]
        decimals = int(self.builder.get_object('spinbutton_round').get_value())

        # Create a CSV reader for the input file.
        reader = csv.DictReader(open(input_file), fieldnames=None,
            delimiter=delimiter, quotechar=quotechar)

        # Show the progress dialog.
        self.pd = ProgressDialog()

        # Set up the data processor.
        t = DataProcessor()
        t.set_csv_reader(reader)
        t.set_property(property)
        t.set_output_folder(output_folder)
        t.set_progress_dialog(self.pd)

        # Set 'round' if 'decimals' set to 0 or higher.
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

        message_finished = self.show_message("Loading data failed!",
            "The data could not be loaded. This is probably caused by "
            "an incorrect input file or the CSV file was in a different "
            "format. If the CSV file was in a different format, "
            "change the settings under Advanced Options accrodingly "
            "and make sure the format matches the format described in the "
            "manual.",
            type=gtk.MESSAGE_ERROR)

    def show_message(self, title, message, type=gtk.MESSAGE_INFO):
        """Show a message dialog showing that input file was not set."""
        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=type,
            buttons=gtk.BUTTONS_OK,
            message_format=title)
        dialog.format_secondary_text(message)
        dialog.set_position(gtk.WIN_POS_CENTER)

        response = dialog.run()
        dialog.destroy()

    def on_about(self, widget, data=None):
        builder = gtk.Builder()
        builder.add_from_file('glade/about.glade')

        about = builder.get_object('about_dialog')
        about.set_version(__version__)
        about.run()
        about.destroy()

    def on_help(button, section):
        """Display the help contents in the system's default web
        browser.
        """

        # Construct the path to the help file.
        path = os.path.abspath(os.path.join('.','docs','user-manual.html'))

        # Turn the path into an URL.
        if path.startswith('/'):
            url = 'file://'+path
        else:
            url = 'file:///'+path

        # Open the URL in the system's web browser.
        webbrowser.open(url)

class DataProcessor(threading.Thread):
    def __init__(self):
        super(DataProcessor, self).__init__()

        self.reader = None
        self.output_folder = None
        self.property = None
        self.dbfile = None
        self.do_round = None
        self.pdialog = None

        self.ecotopes = []
        self.taxa = []
        self.representative_groups = {}
        self.properties = {'density': 'sum_of_density',
            'biomass': 'sum_of_biomass'}

        # Set the path to the database file.
        self.set_directives()

    def set_directives(self):
        """Set the path to the database file."""
        data_path = os.path.expanduser(os.path.join('~','.bioden'))

        # Check if the data folder exists. If not, create it.
        if not os.path.exists(data_path):
            os.makedirs(data_path)

        # Set the path to the database file.
        self.dbfile = os.path.join(data_path, 'data.sqlite')

    def set_progress_dialog(self, pdialog):
        self.pdialog = pdialog

    def set_property(self, property):
        if property in self.properties:
            self.property = property
        else:
            raise ValueError("Property can be either 'density' or "
                "'biomass', not '%s'." % property)

    def set_output_folder(self, output_folder):
        if not os.path.exists(output_folder):
            raise ValueError("Output folder does not exist.")
        self.output_folder = output_folder

    def set_round(self, round_to):
        if not isinstance(round_to, int) or round_to < 0:
            raise ValueError("Argument 'round_to' must be an integer >= 0.")
        self.do_round = round_to

    def set_csv_reader(self, reader):
        """Set the CSV reader."""
        if isinstance(reader, csv.DictReader):
            self.reader = reader
        else:
            raise TypeError("Argument 'reader' must be an instance of 'csv.DictReader'.")

    def update_progress_dialog(self, fraction, action=None, autoclose=True):
        """Set the progress dialog's progressbar fraction to ``fraction``.
        The value of `fraction` should be between 0.0 and 1.0. Optionally set
        the current action to `action`, a short string explaining the current
        action. Optionally set `autoclose` to automatically close the
        progress dialog if `fraction` equals ``1.0``.
        """
        # If no progress dialog is set, do nothing.
        if not self.pdialog:
            return

        # This is always called from a separate thread, so we must use
        # gobject.idle_add to access the GUI.
        gobject.idle_add(self.on_update_progress_dialog, fraction, action, autoclose)

    def on_close_progress_dialog(self, delay=0):
        """Close the progress dialog. Optionally set a delay of `delay`
        seconds before it's being closed.
        """

        # If a delay is set, sleep 'delay' seconds.
        if delay: time.sleep(delay)

        # Close the dialog.
        self.pdialog.dialog.destroy()

        # This callback function must return False, so it is
        # automatically removed from the list of event sources.
        return False

    def on_update_progress_dialog(self, fraction, action=None, autoclose=True):
        """Set the progress dialog's progressbar fraction to ``fraction``.
        The value of `fraction` should be between 0.0 and 1.0. Optionally set
        the current action to `action`, a short string explaining the current
        action. Optionally set `autoclose` to automatically close the
        progress dialog if `fraction` equals ``1.0``.
        """

        # Update fraction.
        self.pdialog.pbar.set_fraction(fraction)

        # Set percentage text for the progress bar.
        percent = fraction * 100.0
        self.pdialog.pbar.set_text("%.0f%%" % percent)

        # Show the current action below the progress bar.
        if isinstance(action, str):
            action = "<span style='italic'>%s</span>" % (action)
            self.pdialog.label_action.set_markup(action)

        if fraction == 1.0:
            self.pdialog.pbar.set_text("Finished!")

            if autoclose:
                # Close the progress dialog when finished. We set a delay
                # of 1 second before closing it.

                # This is always called from a separate thread, so we must
                # use gobject.idle_add to access the GUI.
                gobject.idle_add(self.on_close_progress_dialog, 1)

        # This callback function must return False, so it is
        # automatically removed from the list of event sources.
        return False

    def run(self):
        progress_steps = 7.0

        # Check if all required settings are set.
        self.check_settings()

        self.update_progress_dialog(1/progress_steps,
            "Loading data..."
            )

        # Load the data.
        try:
            self.load_data()
        except:
            # Emit the signal that the process has failed.
            gobject.idle_add(sender.emit, 'load-data-failed')
            return

        self.update_progress_dialog(2/progress_steps,
            "Making sample groups..."
            )

        # Process data for the property.
        self.process()

        self.update_progress_dialog(3/progress_steps,
            "Exporting transponed data..."
            )

        # Export the results.
        self.export_ecotopes_transponed()

        self.update_progress_dialog(4/progress_steps,
            "Exporting raw ecotope data..."
            )

        self.export_ecotopes('raw')

        self.update_progress_dialog(5/progress_steps,
            "Exporting normalized ecotope data..."
            )

        self.export_ecotopes('normalized')

        self.update_progress_dialog(6/progress_steps,
            "Exporting representative sample groups..."
            )

        self.export_representatives()

        self.update_progress_dialog(7/progress_steps, "")

        # Emit the signal that the process was successful.
        gobject.idle_add(sender.emit, 'process-finished')

    def check_settings(self):
        if not self.reader:
            raise ValueError("Attribute 'reader' has not been set.")
        if not self.dbfile:
            raise ValueError("Attribute 'dbfile' has not been set.")
        if not self.property:
            raise ValueError("Attribute 'property' has not been set.")
        if not self.output_folder:
            raise ValueError("Attribute 'output_folder' has not been set.")

        return True

    def load_data(self):
        """Extract the required columns from the CSV data and insert
        these into the database.
        """
        logging.info("Loading data...")

        # Create a new database file.
        self.make_db()

        # The column names.
        fields = ['sample code', 'compiled ecotope',
            'standardised taxon', 'density', 'biomass',
            'sample surface']

        # Alter the above column names to match the ones in the CSV file.
        for i,f in enumerate(fields):
            for name in self.reader.fieldnames:
                if f in name.lower():
                    fields[i] = name
                    break

        # Connect with the database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        # List of sample codes. Used to check which sample codes have
        # already been inserted into the database.
        sample_codes = []

        # Insert CSV data into database.
        for row in self.reader:
            sample_code = int(row[fields[0]])

            # Insert the data into the 'data' table.
            cursor.execute("INSERT INTO data VALUES (null,?,?,?,?,?)",
                (sample_code,
                row[fields[1]],
                row[fields[2]],
                to_float(row[fields[3]]),
                to_float(row[fields[4]])
                ))

            # Check is the current sample code is in the list of sample
            # codes.
            if sample_code not in sample_codes:
                # If not, add it to the list of sample codes, and
                # insert the sample code + surface into the 'samples'
                # table.
                sample_codes.append(sample_code)

                # Sample codes and sample surfaces are saved in a
                # separate table because each sample code is linked
                # to a single sample surface.
                cursor.execute("INSERT INTO samples VALUES (?,?)",
                    ( sample_code, to_float(row[fields[5]]) )
                    )

        # Commit the transaction.
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def make_db(self):
        """Create the database file with the necessary tables."""

        # Delete the current database file.
        if os.path.isfile(self.dbfile):
            self.remove_db_file()

        # This will automatically create a new database file.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        cursor.execute("CREATE TABLE data ( \
            id INTEGER PRIMARY KEY, \
            sample_code INTEGER, \
            compiled_ecotope VARCHAR, \
            standardised_taxon VARCHAR, \
            sum_of_density REAL, \
            sum_of_biomass REAL \
        )")

        cursor.execute("CREATE TABLE samples ( \
            sample_code INTEGER PRIMARY KEY, \
            sample_surface REAL \
        )")

        cursor.execute("CREATE TABLE sums_of ( \
            id INTEGER PRIMARY KEY, \
            group_id INTEGER, \
            compiled_ecotope VARCHAR, \
            standardised_taxon VARCHAR, \
            sum_of REAL, \
            group_surface REAL \
        )")

        cursor.execute("CREATE TABLE normalized_sums_of (\
            id INTEGER PRIMARY KEY, \
            group_id INTEGER, \
            compiled_ecotope VARCHAR, \
            standardised_taxon VARCHAR, \
            sum_of REAL, \
            group_surface REAL \
        )")

        cursor.execute("CREATE TABLE biodiversity ( \
            id INTEGER PRIMARY KEY, \
            compiled_ecotope VARCHAR, \
            group_id INTEGER, \
            diversity INTEGER \
        )")

        # Commit the transaction.
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def remove_db_file(self, tries=0):
        """Remove the database file."""
        if tries > 2:
            raise EnvironmentError("Unable to remove the file %s. "
                "Please make sure it's not in use by a different "
                "process." % self.dbfile)
        try:
            os.remove(self.dbfile)
        except:
            tries += 1
            time.sleep(2)
            self.remove_db_file(tries)
        return True

    def process(self):
        """Calculate the sample groups with a sample surface of 0.2
        and save them to the database.
        """
        logging.info("Processing data for property '%s'..." % self.property)

        # Set the field to select from based on the property.
        self.select_field = self.properties[self.property]

        # This will automatically create a new database file.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()
        cursor2 = connection.cursor()

        # Compile a list of all taxa.
        cursor.execute("SELECT standardised_taxon FROM data")
        for taxon in cursor:
            if taxon[0] not in self.taxa:
                self.taxa.append(taxon[0])

        # Compile a list of all ecotopes.
        cursor.execute("SELECT compiled_ecotope FROM data")
        for ecotope in cursor:
            if ecotope[0] not in self.ecotopes:
                self.ecotopes.append(ecotope[0])

        # Walk through each ecotope.
        for ecotope in self.ecotopes:
            # Create a log message.
            log = "Processing ecotope '%s'..." % ecotope
            logging.info(log)
            #sys.stdout.write(log)

            # Get all sample codes matching the current ecotope.
            cursor.execute("SELECT sample_code "
                "FROM data "
                "WHERE compiled_ecotope = ?",
                (ecotope,))
            sample_codes_for_ecotope = [str(x[0]) for x in cursor]
            sample_codes_for_ecotope = uniqify(sample_codes_for_ecotope)

            # Group the sums into groups with a surface of 0.2 or
            # higher.
            groups = self.make_groups(sample_codes_for_ecotope)

            # Get each group from the sample, and insert the data for
            # that group into the database.
            for group_id, group in enumerate(groups, start=1):
                group_surface, group_data = group

                for taxon, sum_of in group_data.iteritems():
                    cursor2.execute("INSERT INTO sums_of \
                        VALUES (null,?,?,?,?,?)",
                        (group_id, ecotope, taxon,
                        sum_of, group_surface))

            # Make all group surfaces exactly 0.2 and transform the
            # corresponding sums accrodingly.
            normalized_groups = self.normalize_groups(groups)

            # Insert the normalized data into the database as well.
            for group_id, group in enumerate(normalized_groups, start=1):
                group_surface, group_data = group

                for taxon, sum_of in group_data.iteritems():
                    cursor2.execute("INSERT INTO normalized_sums_of \
                        VALUES (null,?,?,?,?,?)",
                        (group_id, ecotope, taxon,
                        sum_of, group_surface))

        # Commit the transaction.
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        cursor2.close()
        connection.close()

    def make_groups(self, sample_codes):
        """Return sample groups with a sample surface of 0.2 or
        higher for the list of sample codes 'sample_codes'.
        """
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()
        cursor2 = connection.cursor()

        # Select sample codes+surfaces for the sample codes in the list
        # 'sample_codes'.
        sample_codes = ",".join(sample_codes)
        cursor.execute("SELECT sample_code, sample_surface "
            "FROM samples "
            "WHERE sample_code "
            "IN (%s)" % sample_codes)

        # This list will contain the dictionaries with sums per taxon
        # for the supplied sample codes.
        groups = []

        # The surface of the current group.
        group_surface = 0.0

        # This dictionary contains the sum per taxon for the
        # current group.
        group_data = {}

        for sample_code,sample_surface in cursor:
            # A group surface is the sum of all sample surfaces that
            # makes up the group. So each time we process a new sample,
            # add that sample's surface to the group surface.
            group_surface += sample_surface

            # Get all taxon data for the current sample.
            cursor2.execute("SELECT standardised_taxon, %s "
                "FROM data "
                "WHERE sample_code = ?" % (self.select_field),
                (sample_code,))

            # Calculate the sums of all taxa we encounter.
            for taxon,sum_of in cursor2:
                if taxon in group_data:
                    group_data[taxon] += sum_of
                else:
                    group_data[taxon] = sum_of

            # Check if we reached the current group's maximum surface.
            if group_surface >= 0.2:
                # When this group reached a group_surface of 0.2 or higher,
                # add it to the 'groups' list. Note that this means that
                # if we don't reach 0.2, the group won't be processed.
                groups.append( [group_surface,group_data] )

                # Reset the current group so we can start a new group.
                group_data = {}
                group_surface = 0.0

        # Close connection with the local database.
        cursor.close()
        cursor2.close()
        connection.close()

        # Return the groups.
        return groups

    def normalize_groups(self, groups):
        """Return a normalized version of sample groups 'groups'. It
        converts the sums of the groups to a sample surface of exactly
        0.2.
        """
        for i, group in enumerate(groups):
            group_surface, group_data = group

            # Skip the calculations for this group if the surface
            # is already 0.2.
            if group_surface == 0.2:
                continue

            for taxon, sum_of in group_data.iteritems():


                # Calculate the factor needed to calculate the sum for a
                # surface of 0.2.
                factor = 0.2 / group_surface

                # Calculate the sum if the factor would be 0.2.
                new_sum_of = sum_of * factor

                # Set the new sum_of value for this taxon in the current
                # group.
                groups[i][1][taxon] = new_sum_of

            # When done with all taxa for this group, set the value for
            # group surface to 0.2.
            groups[i][0] = 0.2

        # Return the normalized groups.
        return groups

    def __determine_biodiversities(self):
        """Calculate the biodiversity for each sample group."""
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        for ecotope in self.ecotopes:
            # Get the number of groups for this ecotope.
            cursor.execute("SELECT group_id \
                FROM sums_of \
                WHERE compiled_ecotope = ?",
                (ecotope,)
                )
            groups = []
            for id in cursor:
                if id[0] not in groups:
                    groups.append(id[0])

            for group_id in groups:
                cursor.execute("SELECT COUNT(standardised_taxon) \
                    FROM sums_of \
                    WHERE compiled_ecotope = ? \
                    AND group_id = ?",
                    (ecotope, group_id)
                    )
                diversity = cursor.fetchone()[0]

                cursor.execute("INSERT INTO biodiversity \
                    VALUES (null,?,?,?)",
                    (ecotope, group_id, diversity)
                    )

        # Commit the transaction.
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def __determine_representative_groups(self):
        """Determine which sample group is the most representative
        for each ecotope by finding which ecotope group's biodiversity
        is closest to the biodiversity median of the ecotope.
        """

        # Determine the biodiversities.
        self.__determine_biodiversities()

        # This will automatically create a new database file.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        # A dictionary containing the median of the biodiversities for
        # each ecotope.
        medians = {}

        for ecotope in self.ecotopes:
            # Get the number of groups for this ecotope.
            cursor.execute("SELECT diversity \
                FROM biodiversity \
                WHERE compiled_ecotope = ?",
                (ecotope,)
                )

            # Get all biodiversities for this ecotope.
            diversities = []
            for diversity in cursor:
                diversities.append(diversity[0])

            # Calculate the median.
            medians[ecotope] = median(diversities)

        for ecotope in self.ecotopes:
            cursor.execute("SELECT diversity, group_id \
                FROM biodiversity \
                WHERE compiled_ecotope = ?",
                (ecotope,)
                )

            # Calculate the differences between the median for this
            # ecotope and all diversities from this ecotope. Save
            # the group_id for the group with the smalles difference.
            smallest_difference = None
            for diversity, group_id in cursor:
                difference = abs(medians[ecotope] - diversity)

                if smallest_difference == None:
                    smallest_difference = difference
                    self.representative_groups[ecotope] = group_id
                    continue

                if difference < smallest_difference:
                    smallest_difference = difference
                    self.representative_groups[ecotope] = group_id

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def generate_csv_ecotope(self, ecotope, data='raw'):
        """Return an iterator which generates the CSV data for ecotope
        `ecotope`.
        """
        if data == 'raw':
            target_table = 'sums_of'
        elif data == 'normalized':
            target_table = 'normalized_sums_of'
        else:
            raise ValueError("Value for 'data' can be either 'raw' or 'normalized', not '%s'." % data)

        # Connect to the database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        yield ['Property:', self.property]

        # Return the first row containing the ecotope name.
        yield ['Ecotope:', ecotope]

        # Get the number of groups for this ecotope.
        cursor.execute("SELECT group_id \
            FROM %s \
            WHERE compiled_ecotope = ?" % target_table,
            (ecotope,)
            )
        group_ids = []
        for id in cursor:
            if id[0] not in group_ids:
                group_ids.append(id[0])
        group_ids.sort()

        # Return third row containing the group numbers.
        row = ['Sample group:']
        row.extend(group_ids)
        yield row

        # Return fourth row containing the group surfaces.
        row = ['Group surface:']
        for group_id in group_ids:
            cursor.execute("SELECT group_surface \
                FROM %s \
                WHERE compiled_ecotope = ? \
                AND group_id = ?" % target_table,
                (ecotope,group_id)
                )
            row.extend(cursor.fetchone())
        yield row

        # Return an empty row.
        yield [None]

        # Return the data rows.
        for taxon in self.taxa:
            row = [taxon]

            cursor.execute("SELECT group_id, sum_of \
                FROM %s \
                WHERE compiled_ecotope = ? \
                AND standardised_taxon = ?" % (target_table),
                (ecotope,taxon)
                )
            sums_of = dict(cursor)

            for group_id in group_ids:
                if group_id in sums_of:
                    sum_of = sums_of[group_id]
                    if isinstance(self.do_round, int):
                        sum_of = round(sum_of, self.do_round)
                    row.append(sum_of)
                else:
                    row.append(None)

            yield row

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def generate_csv_ecotope_transponed(self, ecotope):
        """Return an iterator which generates the CSV data of
        non-grouped data for ecotope `ecotope`.
        """
        if self.property == 'biomass':
            select_field = 'sum_of_biomass'
        else:
            select_field = 'sum_of_density'

        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        # Return the first row containing the property.
        yield ['Property:', self.property]

        # Return the second row containing the ecotope name.
        yield ['Ecotope:', ecotope]

        # Get the record IDs for this ecotope.
        cursor.execute("SELECT sample_code \
            FROM data \
            WHERE compiled_ecotope = ?",
            (ecotope,)
            )
        sample_codes = []
        for id in cursor:
            if id[0] not in sample_codes:
                sample_codes.append(id[0])
        sample_codes.sort()

        # Return third row containing the sample codes.
        row = ['Sample code:']
        row.extend(sample_codes)
        yield row

        # Return fourth row containing the sample surfaces.
        row = ['Sample surface:']
        for sample_code in sample_codes:
            cursor.execute("SELECT sample_surface \
                FROM samples \
                WHERE sample_code = ?",
                (sample_code,)
                )
            sample_surface = cursor.fetchone()[0]
            row.append(sample_surface)
        yield row

        # Return an empty row.
        yield [None]

        # Return the data rows.
        for taxon in self.taxa:
            row = [taxon]

            cursor.execute("SELECT sample_code, %s \
                FROM data \
                WHERE compiled_ecotope = ? \
                AND standardised_taxon = ?" % select_field,
                (ecotope,taxon)
                )
            sums_of = dict(cursor)

            for sample_code in sample_codes:
                if sample_code in sums_of:
                    sum_of = sums_of[sample_code]
                    if isinstance(self.do_round, int):
                        sum_of = round(sum_of, self.do_round)
                    row.append(sum_of)
                else:
                    row.append(None)

            yield row

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def generate_csv_representatives(self):
        """Return an iterator which generates the CSV data with
        only the representative group for each ecotope.
        """

        # Determine the representative group for each ecotope.
        self.__determine_representative_groups()

        # Connect to the database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        yield ['Property:', self.property]

        # Return the first row containing the ecotopes.
        row = ['Ecotope:']
        for ecotope in self.ecotopes:
            row.append(ecotope)
        yield row

        # Return fourth row containing the group surfaces.
        row = ['Group surface:']
        for ecotope in self.ecotopes:
            # Get the most representative group for this ecotope.
            group_id = self.representative_groups[ecotope]

            # Get the group surfaces for this group.
            cursor.execute("SELECT group_surface \
                FROM normalized_sums_of \
                WHERE compiled_ecotope = ? \
                AND group_id = ?",
                (ecotope,group_id)
                )
            row.extend(cursor.fetchone())
        yield row

        # Return an empty row.
        yield [None]

        # Return the data rows.
        for taxon in self.taxa:
            row = [taxon]
            for ecotope in self.ecotopes:
                # Get the most representative group for this ecotope.
                group_id = self.representative_groups[ecotope]

                # Get the sum_of
                cursor.execute("SELECT sum_of \
                    FROM normalized_sums_of \
                    WHERE group_id = ? \
                    AND compiled_ecotope = ? \
                    AND standardised_taxon = ?",
                    (group_id,ecotope,taxon)
                    )

                density = cursor.fetchone()
                if not density:
                    row.append(None)
                else:
                    density = density[0]
                    if isinstance(self.do_round, int):
                        density = round(density, self.do_round)
                    row.append(density)
            yield row

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def export_ecotopes(self, data='raw'):
        for ecotope in self.ecotopes:
            # Create a CSV generator.
            csvgen = self.generate_csv_ecotope(ecotope, data)

            # Construct a filename.
            if data == 'raw':
                prefix = 'raw'
            else:
                prefix = 'ambi'
            suffix = ecotope.replace(" ", "_")
            filename = "%s_%s_%s.csv" % (prefix, self.property, suffix)
            output_file = os.path.join(self.output_folder, filename)

            # Export data.
            logging.info("Saving %s sample groups of ecotope '%s' to %s" % (data, ecotope, output_file))
            self.export_csv(output_file, csvgen)

    def export_ecotopes_transponed(self):
        for ecotope in self.ecotopes:
            # Create a CSV generator.
            csvgen = self.generate_csv_ecotope_transponed(ecotope)

            # Construct a filename.
            suffix = ecotope.replace(" ", "_")
            filename = "transponed_%s_%s.csv" % (self.property, suffix)
            output_file = os.path.join(self.output_folder, filename)

            # Export data.
            logging.info("Saving transponed data of ecotope '%s' to %s" % (ecotope, output_file))
            self.export_csv(output_file, csvgen)

    def export_representatives(self):
        # Create a CSV generator.
        csvgen = self.generate_csv_representatives()

        filename = "representatives_%s.csv" % (self.property)
        output_file = os.path.join(self.output_folder, filename)

        # Export data.
        logging.info("Saving representative sample groups to %s" % (output_file))
        self.export_csv(output_file, csvgen)

    def export_csv(self, output_file, data_generator):
        writer = csv.writer(open(output_file, 'wb'),
            delimiter=',',
            quoting=csv.QUOTE_MINIMAL)
        writer.writerows(data_generator)

if __name__ == '__main__':
    sender = Sender()
    app = MainWindow()
    gtk.main()
    sys.exit(0)
