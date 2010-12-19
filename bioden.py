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
import getopt
import csv
import logging
import random
from sqlite3 import dbapi2 as sqlite

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, GiMaRIS"
__credits__ = ["Serrano Pereira <serrano.pereira@gmail.com>"]
__license__ = "GPL3"
__version__ = "0.1"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2010/12/12"


def main(argv):
    # Show INFO logs.
    logging.basicConfig(level=logging.INFO,
        format='%(levelname)s %(message)s')

    # Default settings.
    has_header = True
    input_file = None
    output_folder = None
    delimiter = ";"
    quotechar = '"'
    property = 'biomass'
    do_round = None

    try:
        opts, args = getopt.getopt(argv, 'hd:q:p:r:i:o:',
            ['help', 'delimiter=', 'quotechar=', 'property=', 'round='])
    except getopt.GetoptError:
        usage()
        sys.exit(1)

    # Handle arguments.
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
        elif opt in ("-i"):
            input_file = arg
        elif opt in ("-o"):
            output_folder = arg
        elif opt in ("-d", "--delimiter"):
            delimiter = arg
        elif opt in ("-q", "--quotechar"):
            quotechar = arg
        elif opt in ("-p", "--property"):
            property = arg
        elif opt in ("-r", "--round"):
            do_round = int(arg)

    if not input_file or not output_folder:
        usage()

    # Check if the input file and output folder exist.
    if not os.path.isfile(input_file):
        sys.exit("Input file does not exist.")
    if not os.path.exists(output_folder):
        sys.exit("Output folder does not exist. Please make it first.")

    # Create a CSV reader for the input file.
    csvfile = open(input_file)
    reader = csv.DictReader(csvfile, fieldnames=None,
        delimiter=delimiter, quotechar=quotechar)

    # Create a data processor.
    p = DataProcessor()
    # Tell the data processor to round values if requested by the user.
    if isinstance(do_round, int):
        p.do_round = do_round
    # Provide the data processor with a CSV reader.
    p.set_csv_reader(reader)
    # Load the data.
    p.load_data()
    # Process data for the property.
    p.process(property)

    # Export the results.
    p.export_ecotopes_transponed(output_folder)
    p.export_ecotopes(output_folder, 'raw')
    p.export_ecotopes(output_folder, 'normalized')
    p.export_representatives(output_folder)

    logging.info("done.")

def usage():
    """Show usage information."""
    print "bioden %s\n" % __version__
    print "Usage: %s [options] -i [input_file] -o [output_folder]\n" % ( os.path.split(sys.argv[0])[1] )
    print "Options:"
    print "   -h,--help                     Show this usage information."
    print "   -i [input_file]               Input CSV file (*.csv)."
    print "   -o [output_folder]            Folder to save the output files in."
    print "   -d,--delimiter \"[char]\"       A one-character string used to\n \
                                separate fields. It defaults to ';'."
    print "   -q,--quotechar \"[char]\"       A one-character string used to quote\n \
                                fields containing special characters.\n \
                                It defaults to '\"'."
    print "   -p,--property [property]      The property on which to perform the\n \
                                calculations. Can be either 'biomass' \n \
                                (default) or 'density'."
    print "   -r,--round [n]                Round values to [n] decimals. Default\n \
                                is not to round."
    sys.exit()

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

class DataProcessor(object):
    def __init__(self):
        self.reader = None
        self.ecotopes = []
        self.taxa = []
        self.do_round = None
        self.properties = {'density': 'sum_of_density',
            'biomass': 'sum_of_biomass'}
        self.property = None
        self.representative_groups = {}

        # Set the path to the database file.
        self.set_directives()

    def set_directives(self):
        """Set the path to the database file."""
        data_path = os.path.expanduser(os.path.join('~','.bioden'))

        # Check if the data folder exists. If not, create it.
        if not os.path.exists(data_path):
            os.makedirs(data_path)

        self.dbfile = os.path.join(data_path, 'data.sqlite')

    def set_csv_reader(self, reader):
        """Set the CSV reader."""
        self.reader = reader

    def load_data(self):
        """Extract the required columns from the CSV data and insert
        these into the database.
        """
        logging.info("Loading data...")

        # Create a new database file.
        self.make_db()

        # The order in which the columns occur in the database 'data'
        # table.
        fields = ['Sample code', 'Compiled ecotope',
            'Standardised Taxon', 'SumOfDensity', 'SumOfBiomass',
            'Sample surface']

        # Alter the above field names to match the ones in the CSV file.
        for i,f in enumerate(fields):
            for name in self.reader.fieldnames:
                if f in name:
                    fields[i] = name
                    break

        # Connect with the database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        # List of sample codes.
        sample_codes = []

        # Insert CSV data into database.
        for row in self.reader:
            sample_code = row[fields[0]]

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
            raise EnvironmentError("I was unable to remove the file %s. "
                "Please make sure it's not in use by a different "
                "process." % self.dbfile)
        try:
            os.remove(self.dbfile)
        except:
            tries += 1
            time.sleep(2)
            self.remove_db_file(tries)
        return True

    def process(self, property):
        """Calculate the sample groups with a sample surface of 0.2
        and save them to the database.
        """
        logging.info("Processing data for property '%s'..." % property)

        # Get the table names from which to select data from the
        # database based on 'property'.
        if property in self.properties:
            self.property = property
            self.select_field = self.properties[property]
        else:
            raise ValueError("Value of 'property' must be either 'density' or 'biomass'.")

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

    def export_ecotopes(self, output_folder, data='raw'):
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
            output_file = os.path.join(output_folder, filename)

            # Export data.
            logging.info("Saving %s sample groups of ecotope '%s' to %s" % (data, ecotope, output_file))
            self.export_csv(output_file, csvgen)

    def export_ecotopes_transponed(self, output_folder):
        for ecotope in self.ecotopes:
            # Create a CSV generator.
            csvgen = self.generate_csv_ecotope_transponed(ecotope)

            # Construct a filename.
            suffix = ecotope.replace(" ", "_")
            filename = "transponed_%s_%s.csv" % (self.property, suffix)
            output_file = os.path.join(output_folder, filename)

            # Export data.
            logging.info("Saving transponed data of ecotope '%s' to %s" % (ecotope, output_file))
            self.export_csv(output_file, csvgen)

    def export_representatives(self, output_folder):
        # Create a CSV generator.
        csvgen = self.generate_csv_representatives()

        filename = "representatives_%s.csv" % (self.property)
        output_file = os.path.join(output_folder, filename)

        # Export data.
        logging.info("Saving representative sample groups to %s" % (output_file))
        self.export_csv(output_file, csvgen)

    def export_csv(self, output_file, data_generator):
        writer = csv.writer(open(output_file, 'wb'),
            delimiter=',',
            quoting=csv.QUOTE_MINIMAL)
        writer.writerows(data_generator)

if __name__ == "__main__":
    main(sys.argv[1:])

sys.exit()
