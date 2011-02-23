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
import time
import threading
from sqlite3 import dbapi2 as sqlite
import csv

import gobject
import xlrd

import bioden.std
import bioden.exporter

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__credits__ = ["Serrano Pereira <serrano.pereira@gmail.com>"]
__license__ = "GPL3"
__version__ = "0.3"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2011/02/18"


class DataProcessor(threading.Thread):
    def __init__(self):
        super(DataProcessor, self).__init__()

        self._input_file = None
        self._reader = None
        self._output_folder = None
        self._property = None
        self._dbfile = None
        self._do_round = None
        self._target_sample_surface = 0.2
        self._output_format = 'csv'
        self._pdialog = None
        self.pdialog_handler = bioden.std.ProgressDialogHandler()
        self._representative_groups = {}
        self._properties = {'density': 'sum_of_density',
            'biomass': 'sum_of_biomass'}
        self.ecotopes = []
        self.taxa = []
        self.csv_dialect = csv.excel

        # Set the path to the database file.
        self.set_directives()

    def set_input_file(self, filename, type):
        """Set the input file and type."""
        supported_types = ('csv','xls')
        if type not in supported_types:
            raise ValueError("Possible values for 'type' are 'csv' and 'xls', not '%s'." % type)
        self._input_file = (filename, type)

    def set_csv_dialect(self, delimiter, quotechar):
        self.csv_dialect = csv.excel
        self.csv_dialect.delimiter = delimiter
        self.csv_dialect.quotechar = quotechar

    def create_reader(self):
        """Set a file reader from the input file and type."""
        if self._input_file[1] == "csv":
            reader = csv.DictReader(open(self._input_file[0]), dialect=self.csv_dialect,
                fieldnames=None)
            self.set_reader(reader)
        elif self._input_file[1] == "xls":
            book = xlrd.open_workbook(self._input_file[0])
            self.set_reader(book)

    def set_directives(self):
        """Set the path to the database file."""
        data_path = os.path.expanduser(os.path.join('~','.bioden'))

        # Check if the data folder exists. If not, create it.
        if not os.path.exists(data_path):
            os.makedirs(data_path)

        # Set the path to the database file.
        self._dbfile = os.path.join(data_path, 'data.sqlite')

    def set_progress_dialog(self, pdialog):
        self._pdialog = pdialog
        self.pdialog_handler.set_progress_dialog(pdialog)

    def set_property(self, property):
        if property in self._properties:
            self._property = property
        else:
            raise ValueError("Property can be either 'density' or "
                "'biomass', not '%s'." % property)

    def set_output_folder(self, output_folder):
        if not os.path.exists(output_folder):
            raise ValueError("Output folder does not exist.")
        self._output_folder = output_folder

    def set_round(self, round_to):
        if not isinstance(round_to, int) or round_to < 0:
            raise ValueError("Argument 'round_to' must be an integer >= 0.")
        self._do_round = round_to

    def set_target_sample_surface(self, surface):
        if not isinstance(surface, float) or surface <= 0:
            raise ValueError("Argument 'surface' must be a float > 0.")
        self._target_sample_surface = surface

    def set_output_format(self, format):
        formats = ('csv', 'xls')
        if format not in formats:
            raise ValueError("Possible formats are 'csv' and 'xls', not '%s'." % format)
        self._output_format = format

    def run(self):
        # Create a CSV or XSL generator.
        if self._output_format == 'csv':
            generator = bioden.exporter.CSVExporter(self)
        elif self._output_format == 'xls':
            generator = bioden.exporter.XLSExporter(self)

        # Check if all required settings are set.
        self.check_settings()

        # Load the data.
        self.pdialog_handler.set_action("Loading data...")
        self.pdialog_handler.add_details("Loading data...")
        try:
            # Create and set the file reader.
            self.create_reader()

            # Load the data.
            self.load_data()
        except Exception as strerror:
            # Emit the signal that the process has failed.
            gobject.idle_add(bioden.std.sender.emit, 'load-data-failed', strerror)
            return

        # Pre-process some data. This will populate self.ecotopes, which
        # is needed now by the progress dialog handler.
        self.pre_process()

        # Set the number of times we will call pdialog_handler.increase().
        steps = 7 + (len(self.ecotopes) * 4)
        self.pdialog_handler.set_total_steps(steps)

        # Process data for the property 'self._property'.
        self.pdialog_handler.increase("Making sample groups for property '%s'..." % (self._property))
        # Here, pdialog_handler.increase will be called for each ecotope.
        self.process()

        # Export the results.
        self.pdialog_handler.increase("Exporting non-grouped ecotope data...")
        # Here, pdialog_handler.increase will be called for each ecotope.
        generator.export_ecotopes_raw()

        self.pdialog_handler.increase("Exporting raw ecotope groups...")
        # Here, pdialog_handler.increase will be called for each ecotope.
        generator.export_ecotopes_grouped('raw')

        self.pdialog_handler.increase("Exporting normalized ecotope groups...")
        # Here, pdialog_handler.increase will be called for each ecotope.
        generator.export_ecotopes_grouped('normalized')

        self.pdialog_handler.increase("Determining representative sample group for each ecotope...")
        self.determine_representative_groups()

        self.pdialog_handler.increase("Exporting representative sample groups...")
        generator.export_representatives()

        self.pdialog_handler.increase("")

        # Emit the signal that the process was successful.
        gobject.idle_add(bioden.std.sender.emit, 'process-finished')

    def check_settings(self):
        if not self._input_file:
            raise ValueError("Attribute 'input_file' has not been set.")
        if not self._dbfile:
            raise ValueError("Attribute 'dbfile' has not been set.")
        if not self._property:
            raise ValueError("Attribute 'property' has not been set.")
        if not self._output_folder:
            raise ValueError("Attribute 'output_folder' has not been set.")

        return True

    def make_db(self):
        """Create the database file with the necessary tables."""

        # Delete the current database file.
        if os.path.isfile(self._dbfile):
            self.remove_db_file()

        # This will automatically create a new database file.
        connection = sqlite.connect(self._dbfile)
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
                "process." % self._dbfile)
        try:
            os.remove(self._dbfile)
        except:
            tries += 1
            time.sleep(2)
            self.remove_db_file(tries)
        return True

    def pre_process(self):
        # This will automatically create a new database file.
        connection = sqlite.connect(self._dbfile)
        cursor = connection.cursor()

        # Compile a list of all taxa.
        cursor.execute("SELECT standardised_taxon FROM data")
        for taxon in cursor:
            if taxon[0] not in self.taxa:
                self.taxa.append(taxon[0])

        # Compile a list of all ecotopes.
        cursor.execute("SELECT compiled_ecotope FROM data")
        for ecotope in cursor:
            # Convert ecotopes to lower case to account for upper/lowercase
            # differences.
            ecotope = ecotope[0].lower()

            if ecotope not in self.ecotopes:
                self.ecotopes.append(ecotope)

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def process(self):
        """Calculate the sample groups with a sample surface of
        'self._target_sample_surface' and save them to the database.
        """
        log = "Processing data for property '%s'..." % self._property
        self.pdialog_handler.add_details(log)

        # Set the field to select from based on the property.
        self.select_field = self._properties[self._property]

        # This will automatically create a new database file.
        connection = sqlite.connect(self._dbfile)
        cursor = connection.cursor()

        # Walk through each ecotope.
        for ecotope in self.ecotopes:
            # Update the progress dialog.
            self.pdialog_handler.increase()

            # Create a log message.
            log = "Processing ecotope '%s'..." % ecotope
            self.pdialog_handler.add_details(log)

            # Get all sample codes matching the current ecotope.
            cursor.execute("SELECT sample_code "
                "FROM data "
                "WHERE compiled_ecotope = ?",
                (ecotope,))

            sample_codes_for_ecotope = []
            for sample_code in cursor:
                sample_code = str(sample_code[0])
                if sample_code not in sample_codes_for_ecotope:
                    sample_codes_for_ecotope.append(sample_code)

            # Group the sums into groups with a surface of
            # 'self._target_sample_surface' or higher.
            groups = self.make_groups(sample_codes_for_ecotope)

            # Get each group from the sample, and insert the data for
            # that group into the database.
            for group_id, group in enumerate(groups, start=1):
                # Unpack each raw group.
                group_surface, group_data = group

                # Unpack group data and insert it into the database.
                for taxon, sum_of in group_data.iteritems():
                    cursor.execute("INSERT INTO sums_of \
                        VALUES (null,?,?,?,?,?)",
                        (group_id, ecotope, taxon,
                        sum_of, group_surface))

            # Make normalized groups out of the raw groups.
            # Make all group surfaces exactly 'self._target_sample_surface' and
            # transform the corresponding sums accrodingly.
            normalized_groups = self.normalize_groups(groups)

            # Insert the normalized data into the database as well.
            for group_id, group in enumerate(normalized_groups, start=1):
                # Unpack each normalized group.
                group_surface, group_data = group

                # Unpack group data and insert it into the database.
                for taxon, sum_of in group_data.iteritems():
                    cursor.execute("INSERT INTO normalized_sums_of \
                        VALUES (null,?,?,?,?,?)",
                        (group_id, ecotope, taxon,
                        sum_of, group_surface))

        # Commit the transaction.
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def make_groups(self, sample_codes):
        """Return sample groups with a sample surface of
        `self._target_sample_surface` or higher for the list of sample codes
        `sample_codes`.
        """
        connection = sqlite.connect(self._dbfile)
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
            if group_surface >= self._target_sample_surface:
                # When this group reached a group_surface of
                # 'self._target_sample_surface' or higher, add it to the
                # 'groups' list. Note that this means that if we don't reach
                # 'self._target_sample_surface', the group won't be processed.
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
        """Return a normalized version of sample groups `groups`. It
        converts the sums of the groups to a sample surface of exactly
        `self._target_sample_surface`.
        """
        for i, group in enumerate(groups):
            # Unpack current group.
            group_surface, group_data = group

            # Skip the calculations for this group if the surface
            # is already equal to 'self._target_sample_surface'.
            if group_surface == self._target_sample_surface:
                continue

            # Calculate the factor needed to calculate the sum for a
            # surface of 'self._target_sample_surface' for each group.
            factor = self._target_sample_surface / group_surface

            # Unpack group data.
            for taxon, sum_of in group_data.iteritems():
                # Calculate the sum if the group surface would be
                # 'self._target_sample_surface'.
                new_sum_of = sum_of * factor

                # Set the new sum_of value for this taxon in the current
                # group.
                groups[i][1][taxon] = new_sum_of

            # When done with all taxa for this group, set the value for
            # group surface to 'self._target_sample_surface'.
            groups[i][0] = self._target_sample_surface

        # Return the normalized groups.
        return groups

    def __determine_biodiversities(self):
        """Calculate the biodiversity for each sample group."""
        connection = sqlite.connect(self._dbfile)
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
                # We define the biodiversity for each group by looking
                # up the number of taxa registered by that group ID and
                # ecotope.
                # Note: We exclude the taxa which have a 'sum of' of 0.
                cursor.execute("SELECT COUNT(standardised_taxon) \
                    FROM sums_of \
                    WHERE compiled_ecotope = ? \
                    AND group_id = ? \
                    AND sum_of > 0",
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

    def determine_representative_groups(self):
        """Determine which sample group is the most representative
        for each ecotope by finding which ecotope group's biodiversity
        is closest to the biodiversity median of the ecotope.
        """

        # Determine the biodiversities.
        self.__determine_biodiversities()

        # Connect to the database.
        connection = sqlite.connect(self._dbfile)
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

            # Skip this ecotope if there were no diversities found, and thus
            # no groups.
            if len(diversities) == 0:
                continue

            # Calculate the median.
            medians[ecotope] = bioden.std.median(diversities)

        for ecotope in self.ecotopes:
            cursor.execute("SELECT diversity, group_id \
                FROM biodiversity \
                WHERE compiled_ecotope = ?",
                (ecotope,)
                )

            # Calculate the differences between the diversity median for
            # this ecotope and all diversities from this ecotope. Save
            # the group_id for the group with the smalles difference.
            smallest_difference = None
            for diversity, group_id in cursor:
                difference = abs(medians[ecotope] - diversity)

                if smallest_difference == None:
                    smallest_difference = difference
                    self._representative_groups[ecotope] = group_id
                elif difference < smallest_difference:
                    smallest_difference = difference
                    self._representative_groups[ecotope] = group_id

        # Close connection with the local database.
        cursor.close()
        connection.close()

class CSVProcessor(DataProcessor):
    """Process CSV data."""

    def set_reader(self, reader):
        """Set the CSV reader."""
        if isinstance(reader, csv.DictReader):
            self._reader = reader
        else:
            raise TypeError("Argument 'reader' must be an instance of 'csv.DictReader'.")

    def load_data(self):
        """Extract the required columns from the CSV data and insert
        these into the database.
        """
        # Create a new database file.
        self.make_db()

        # The required field names.
        fields = {'sample code': None, 'compiled ecotope': None,
            'standardised taxon': None, 'density': None, 'biomass': None,
            'sample surface': None}

        # Update the values in the 'fields' dictionary to the index number
        # for the corresponding field in the CSV file.
        fieldnames = self._reader.fieldnames
        for f in fields:
            for name in fieldnames:
                if f in name.lower():
                    fields[f] = name
                    break

        # Connect with the database.
        connection = sqlite.connect(self._dbfile)
        cursor = connection.cursor()

        # List of sample codes. Used to check which sample codes have
        # already been inserted into the database.
        sample_codes = []

        # Insert CSV data into database.
        for row in self._reader:
            sample_code = int(row[fields['sample code']])

            # Insert the data into the 'data' table.
            if self._property == 'density':
                if not fields['density']:
                    raise ValueError("The data file is missing the 'density' column.")

                cursor.execute("INSERT INTO data VALUES (null,?,?,?,?,null)",
                    (sample_code,
                    row[fields['compiled ecotope']].lower(), # Save ecotopes in lower case.
                    row[fields['standardised taxon']],
                    bioden.std.to_float(row[fields['density']])
                    ))
            elif self._property == 'biomass':
                if not fields['biomass']:
                    raise ValueError("The data file is missing the 'biomass' column.")

                cursor.execute("INSERT INTO data VALUES (null,?,?,?,null,?)",
                    (sample_code,
                    row[fields['compiled ecotope']].lower(), # Save ecotopes in lower case.
                    row[fields['standardised taxon']],
                    bioden.std.to_float(row[fields['biomass']])
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
                    ( sample_code, bioden.std.to_float(row[fields['sample surface']]) )
                    )

        # Commit the transaction.
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        connection.close()

class XLSProcessor(DataProcessor):
    """Process XSL data."""

    def set_reader(self, book):
        """Set the XSL reader."""
        if isinstance(book, xlrd.Book):
            # By default, use the first sheet in the Excel file.
            self._reader = self.sheet = book.sheets()[0]
        else:
            raise TypeError("Argument 'book' must be an instance of 'xlrd.Book'.")

    def load_data(self):
        """Extract the required columns from the CSV data and insert
        these into the database.
        """
        # Create a new database file.
        self.make_db()

        # The required field names.
        fields = {'sample code': None, 'compiled ecotope': None,
            'standardised taxon': None, 'density': None, 'biomass': None,
            'sample surface': None}

        # Update the values in the 'fields' dictionary to the index number
        # for the corresponding field in the XSL file.
        fieldnames = self.sheet.row_values(0)
        for f in fields:
            for name in fieldnames:
                if f in name.lower():
                    fields[f] = fieldnames.index(name)
                    break

        # Connect with the database.
        connection = sqlite.connect(self._dbfile)
        cursor = connection.cursor()

        # List of sample codes. Used to check which sample codes have
        # already been inserted into the database.
        sample_codes = []

        # Insert CSV data into database.
        for row_n in range(self.sheet.nrows):
            # Skip the first row, as this row contains the field names.
            if row_n == 0:
                continue

            # Get the values for the current row.
            row = self.sheet.row_values(row_n)

            # Get the sample code from the current row.
            sample_code = int(row[fields['sample code']])

            # Insert the data into the 'data' table.
            if self._property == 'density':
                if not fields['density']:
                    raise ValueError("The data file is missing the 'density' column.")

                cursor.execute("INSERT INTO data VALUES (null,?,?,?,?,null)",
                    (sample_code,
                    row[fields['compiled ecotope']].lower(), # Save ecotopes in lower case.
                    row[fields['standardised taxon']],
                    bioden.std.to_float(row[fields['density']])
                    ))
            elif self._property == 'biomass':
                if not fields['biomass']:
                    raise ValueError("The data file is missing the 'biomass' column.")

                cursor.execute("INSERT INTO data VALUES (null,?,?,?,null,?)",
                    (sample_code,
                    row[fields['compiled ecotope']].lower(), # Save ecotopes in lower case.
                    row[fields['standardised taxon']],
                    bioden.std.to_float(row[fields['biomass']])
                    ))

            # Check if the current sample code is in the list of sample
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
                    ( sample_code, bioden.std.to_float(row[fields['sample surface']]) )
                    )

        # Commit the transaction.
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        connection.close()
