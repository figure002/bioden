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

import time

from gi.repository import GObject

def to_float(x):
    """Return the float from a number which uses a comma as the decimal
    separator."""
    if isinstance(x, str):
        x = float(x.replace(',','.'))
    return x

def median(values):
    """Return the median of a series of numbers."""
    values = sorted(values)
    count = len(values)

    if count == 0:
        raise ValueError("Argument 'values' was an empty list.")

    if count % 2 == 1:
        return values[(count+1)/2-1]
    else:
        lower = values[count/2-1]
        upper = values[count/2]
        return (float(lower + upper)) / 2

class Sender(GObject.GObject):
    """Custom GObject for emitting custom signals."""
    __gproperties__ = {
        'strerror' : (GObject.TYPE_STRING, # type
            "Error message", # nick name
            "The error message returned by a function or class.", # description
            '', # default value
            GObject.PARAM_READWRITE), # flags
    }

    __gsignals__ = {
        'process-finished': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'load-data-failed': (GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_STRING,)),
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        self.strerror = ''

    def do_get_property(self, property):
        if property.name == 'strerror':
            return self.strerror
        else:
            raise AttributeError('Unknown property %s' % property.name)

    def do_set_property(self, property, value):
        if property.name == 'strerror':
            self.strerror = value
        else:
            raise AttributeError('Unknown property %s' % property.name)



class ProgressDialogHandler:
    """This class allows you to control the progress dialog from a separate
    thread.
    """

    def __init__(self, pdialog=None):
        self.total_steps = None
        self.current_step = 0
        self.autoclose = True
        self.pdialog = pdialog

    def set_progress_dialog(self, pdialog):
        self.pdialog = pdialog

    def set_total_steps(self, number):
        """Set the total number of steps for the progress."""
        if not isinstance(number, int):
            raise ValueError("Value for 'number' should be an integer, not '%s'." %
                (type(number).__name__))

        # Reset the current step so we start with 0% again.
        self.current_step = 0

        # Set the new value for total steps. This number must be saved as a
        # float, because we want to calculate fractions.
        self.total_steps = float(number)

    def set_action(self, text):
        """Set the progress dialog's action string to `text`. This action
        string is showed in italics below the progress bar.
        """
        text = "<span style='italic'>%s</span>" % (text)
        GObject.idle_add(self.pdialog.label_action.set_markup, text)

    def increase(self, action=None):
        """Increase the progress bar's fraction. Calling this method causes
        the progress bar to fill a portion of the bar. This method takes care
        of calculating the right fraction. If `action` is supplied, the
        progress dialog's action string is set to `action`.
        """
        if not self.total_steps:
            raise ValueError("You didn't set the total number of steps. Use "
                "'set_total_steps()'.")

        # Calculate the new fraction.
        self.current_step += 1
        fraction = self.current_step / self.total_steps

        # Check if the fraction has a logical value.
        if 0.0 > fraction > 1.0:
            raise ValueError("Incorrect fraction '%f' encountered. You "
                "probably didn't set the correct total steps." % fraction)

        # Update the progress dialog.
        self.update(fraction, action)

    def update(self, fraction, action=None):
        """Set the progress dialog's progress bar fraction to `fraction`.
        The value of `fraction` should be between 0.0 and 1.0. Optionally set
        the current action to `action`, a short string explaining the current
        action.

        The "progress-dialog" configuration must be set to an instance of
        :class:`setlyze.gui.ProgressDialog` for this to work. If no progress
        dialog is set, nothing will happen.
        """
        # If no progress dialog is set, do nothing.
        if not self.pdialog:
            return

        # In case this is always called from a separate thread, so we must use
        # GObject.idle_add to access the GUI.
        GObject.idle_add(self.__update_progress_dialog, fraction, action)

    def __update_progress_dialog(self, fraction, action=None):
        """Set the progress dialog's progressbar fraction to `fraction`.
        The value of `fraction` should be between 0.0 and 1.0. Optionally set
        the current action to `action`, a short string explaining the current
        action.

        Don't call this function manually; use :meth:`increase` instead.
        """

        # Update fraction.
        self.pdialog.pbar.set_fraction(fraction)

        # Set percentage text for the progress bar.
        percent = fraction * 100.0
        self.pdialog.pbar.set_text("%.1f%%" % percent)

        # Show the current action below the progress bar.
        if isinstance(action, str):
            action = "<span style='italic'>%s</span>" % (action)
            self.pdialog.label_action.set_markup(action)

        if fraction == 1.0:
            self.pdialog.pbar.set_text("Finished!")

            if self.autoclose:
                # Close the progress dialog when finished. We set a delay
                # of 1 second before closing it, so the user gets to see the
                # dialog when an analysis finishes very fast.

                # This is always called from a separate thread, so we must
                # use GObject.idle_add to access the GUI.
                GObject.idle_add(self.__close_progress_dialog, 1)

        # This callback function must return False, so it is
        # automatically removed from the list of event sources.
        return False

    def __close_progress_dialog(self, delay=0):
        """Close the progress dialog. Optionally set a delay of `delay`
        seconds before it's being closed.

        There's no need to call this function manually, as it is called
        by :meth:`__update_progress_dialog` when needed.
        """

        # If a delay is set, sleep 'delay' seconds.
        if delay: time.sleep(delay)

        # Close the progress dialog.
        self.pdialog.destroy()

        # This callback function must return False, so it is
        # automatically removed from the list of event sources.
        return False

    def add_details(self, text):
        """Add `text` to the progress dialog's details text box."""

        # If no progress dialog is set, do nothing.
        if not self.pdialog:
            return

        # Add a newline at the end of 'text'.
        text += "\n"

        # This is always called from a separate thread, so we must use
        # GObject.idle_add to access the GUI.
        GObject.idle_add(self.__on_add_details, text)

    def __on_add_details(self, text):
        """Add `text` to the progress dialog's details text box. This
        function is called by :meth:`update_progress_details`, and
        should not be called manually."""

        # Update text for the details textview.
        self.pdialog.textbuffer.insert_at_cursor(text)

        # Scroll to the bottom of the textview.
        self.pdialog.textview.scroll_mark_onscreen(self.pdialog.textbuffer.get_insert())

        # This callback function must return False, so it is
        # automatically removed from the list of event sources.
        return False

sender = Sender()
