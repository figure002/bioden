#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2010, 2011, GiMaRIS <info@gimaris.com>
#
#  This file is part of BioDen - A data normalizer and transponer for
#  files containing taxon biomass/density data for ecotopes.
#
#  SETLyze is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SETLyze is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import csv
from sqlite3 import dbapi2 as sqlite

import xlrd
import xlwt

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__credits__ = ["Serrano Pereira <serrano.pereira@gmail.com>"]
__license__ = "GPL3"
__version__ = "0.3"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2011/02/18"


class Generator:
    """Super class for Generator classes."""

    def __init__(self, processor):
        self.processor = processor
        self.dbfile = processor.dbfile
        self.property = processor.property
        self.taxa = processor.taxa
        self.ecotopes = processor.ecotopes
        self.representative_groups = processor.representative_groups
        self.do_round = processor.do_round
        self.output_folder = processor.output_folder
        self.file_extension = ".txt"

    def ecotope_data_grouped(self, ecotope, data_type='raw'):
        """Return a iterator object which generates the CSV data of
        grouped data for ecotope `ecotope`.
        """
        if data_type == 'raw':
            target_table = 'sums_of'
        elif data_type == 'normalized':
            target_table = 'normalized_sums_of'
        else:
            raise ValueError("Value for 'data' can be either 'raw' or 'normalized', not '%s'." % data_type)

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

    def ecotope_data_raw(self, ecotope):
        """Return a iterator object which generates the CSV data of
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

    def representatives(self):
        """Return a iterator object which generates the CSV data with
        only the representative group for each ecotope.
        """
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
            # Append and empty field if the ecotope has no group.
            if ecotope not in self.representative_groups:
                row.append(None)
                continue

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
                # Append and empty field if the ecotope has no group.
                if ecotope not in self.representative_groups:
                    row.append(None)
                    continue

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

    def export_ecotopes_grouped(self, data_type='raw'):
        """Return a iterator object which generates CSV data for all ecotopes.
        For each ecotope, the grouped data is returned. If `data_type` is set
        to "raw", the non-normalized group values are returned. If `data_type`
        is set to "normalized", the normalized group values are returned.
        """
        for ecotope in self.ecotopes:
            # Update progress dialog.
            self.processor.pdialog_handler.increase()

            # Create a CSV generator.
            data = self.ecotope_data_grouped(ecotope, data_type)

            # Construct a filename.
            if data_type == 'raw':
                prefix = 'grouped'
            elif data_type == 'normalized':
                prefix = 'ambi'
            else:
                raise ValueError("Value for 'data' can be either 'raw' or 'normalized', not '%s'." % data_type)

            suffix = ecotope.replace(" ", "_")
            filename = "%s_%s_%s%s" % (prefix, self.property, suffix, self.file_extension)
            output_file = os.path.join(self.output_folder, filename)

            # Export data.
            self.processor.pdialog_handler.add_details("Saving %s sample groups of ecotope '%s' to %s" % (data_type, ecotope, output_file))
            self.export(output_file, data)

    def export_ecotopes_raw(self):
        """Return a iterator object which generates CSV data for all ecotopes.
        For each ecotope, the non-grouped data is returned.
        """
        for ecotope in self.ecotopes:
            # Update progress dialog.
            self.processor.pdialog_handler.increase()

            # Create a CSV generator.
            data = self.ecotope_data_raw(ecotope)

            # Construct a filename.
            suffix = ecotope.replace(" ", "_")
            filename = "raw_%s_%s%s" % (self.property, suffix, self.file_extension)
            output_file = os.path.join(self.output_folder, filename)

            # Export data.
            self.processor.pdialog_handler.add_details("Saving raw data of ecotope '%s' to %s" % (ecotope, output_file))
            self.export(output_file, data)

    def export_representatives(self):
        """Return a iterator object which generates CSV data for all ecotopes.
        For each ecotope, only the representative group is returned.
        """
        # Create a CSV generator.
        data = self.representatives()

        filename = "representatives_%s%s" % (self.property, self.file_extension)
        output_file = os.path.join(self.output_folder, filename)

        # Export data.
        self.processor.pdialog_handler.add_details("Saving representative sample groups to %s" % (output_file))
        self.export(output_file, data)

class CSVExporter(Generator):
    """Export data in CSV format."""

    def __init__(self, processor):
        Generator.__init__(self, processor)
        self.file_extension = ".csv"

    def export(self, output_file, data):
        """Write CSV data `data` to file `output_file`. For better performance,
        'data' should be a iterator object.
        """
        writer = csv.writer(open(output_file, 'wb'),
            delimiter=',',
            quoting=csv.QUOTE_MINIMAL)
        writer.writerows(data)

class XLSExporter(Generator):
    """Export data in XLS format."""

    def __init__(self, processor):
        Generator.__init__(self, processor)
        self.file_extension = ".xls"

    def export(self, output_file, data):
        """Write CSV data `data` to file `output_file`. For better performance,
        'data' should be a iterator object.
        """
        wb = xlwt.Workbook()
        ws = wb.add_sheet('data')
        result = self.write_rows(ws, data)
        wb.save(output_file)

        if not result:
            print "Reached maximum of 256 columns for %s. Only the first 256 columns have been exported." % output_file

    def write_rows(self, work_sheet, data):
        out = True
        for r, row in enumerate(data):
            for c, value in enumerate(row):
                if c >= 256:
                    # Break the current row, because Excel doesn't support 256+ columns.
                    out = False
                    break
                work_sheet.write(r, c, value)
        return out
