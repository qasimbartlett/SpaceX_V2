"""
Created on: March 20, 2024
@author: qasimm@

The overall logic:
  Read all s2p files.
  For each file determine if it is a good filter
"""

from typing import Set, Any

import skrf as rf
import matplotlib.pyplot as plt
import numpy as np
import re
from collections import defaultdict


class FrequencyBand(object):
    def __init__(self, s2p_file, network, frequencies_file, band_low, band_high):
        self.s2p_file = s2p_file
        self.network = network
        self.band_low = band_low
        self.band_high = band_high

        self.frequencies = self.network.frequency
        self.s21_db = self.network.s21.s_db

        self.list_of_frequencies = self.read_list_of_frequencies_from_text_file(frequencies_file)
        self.frequency_db_dict = self.extract_frequencies_db_in_band(self.band_low, self.band_high)

    def extract_frequencies_db_in_band(self, left, right):
        print('-------- extract_frequencies_db_in_band', left, right)
        frequency_db_dict = defaultdict(float)
        for s21_db_value, frequency_value in zip(self.s21_db, self.frequencies):
            frequency_value_only = float(re.sub('-.*', '', str(frequency_value)))
            s21_db_value = float(str(s21_db_value).replace('[', '').replace(']', ''))
            # if len(frequency_value_only) > 1:
            if left < frequency_value_only < right:
                print(f'{self.s2p_file}:: {frequency_value_only}  {s21_db_value}')
                frequency_db_dict[frequency_value_only] = s21_db_value
        return frequency_db_dict

    def read_list_of_frequencies_from_text_file(self, file_name):
        with open(file_name, "r") as f:
            lines = f.readlines()
        lines = [float(string) for string in lines]
        return sorted(list(set(lines)))

    def is_filter_good_in_this_band(self, title, low_db, high_db):
        print(f"\n\n============ {title} ===========")
        good = 1

        for freq in self.list_of_frequencies:
            print('is_filter_good?:', title, self.s2p_file, ' Frequency:', freq, ':db=', self.frequency_db_dict[freq],
                  'Expected db range', high_db, low_db)
            if low_db < self.frequency_db_dict[freq] < high_db:
                good = 1
            else:
                good = 0
                print('is_filter_good?:', title, self.s2p_file, ' NO:  Frequency:', freq, ':db=', self.frequency_db_dict[freq],
                      'Expected db range', high_db, low_db)
                break
        print(self.s2p_file, " is good in ", title, "  ", good)
        return good

    def return_frequency_db_in_this_band(self):
        return self.frequency_db_dict



class S2p(object):
    def __init__(self, s2p_file='x6.s2p'):
        self.s2p_file = s2p_file
        self.network = rf.Network(self.s2p_file)
        self.s21_db = self.network.s21.s_db
        self.frequencies = self.network.frequency

        self.pass_band = FrequencyBand(self.s2p_file, self.network, "pass_band_frequencies", 6.25, 6.75)
        self.stop_band_left = FrequencyBand(self.s2p_file, self.network, "stop_band_left_frequencies", 5.4, 5.7)
        self.stop_band_right = FrequencyBand(self.s2p_file, self.network, "stop_band_right_frequencies", 7.3, 7.6)

        self.pass_band_stop_band_frequencies_db = (self.pass_band.return_frequency_db_in_this_band() |
                                                 (self.stop_band_left.return_frequency_db_in_this_band()
                                                  | self.stop_band_right.return_frequency_db_in_this_band()))
        # Clear the current figure
        plt.clf()
        # Plot the s graph
        self.network.plot_s_db()
        # Save the plot to a file
        plt.savefig(f'{self.s2p_file}.png')

    def is_filter_good(self, pass_band_low_db, pass_band_high_db, stop_band_low_db, stop_band_high_db):
        print(f"\n\n=======================")
        good = 0
        good_pass_band = self.pass_band.is_filter_good_in_this_band("PASS_BAND", pass_band_low_db, pass_band_high_db)
        good_stop_band_left = self.stop_band_left.is_filter_good_in_this_band("STOP_BAND_LEFT", stop_band_low_db, stop_band_high_db)
        good_stop_band_right = self.stop_band_right.is_filter_good_in_this_band("STOP_BAND_RIGHT", stop_band_low_db, stop_band_high_db)

        if good_pass_band and good_stop_band_left and good_stop_band_right:
            good = 1

        print(f'{self.s2p_file}: is good in all bands?{good}. good_pass_band={good_pass_band}, '
              f'good_stop_band_left={good_stop_band_left} and good_stop_band_right={good_stop_band_right};  '
              f'PASS_BAND_Thresholds={pass_band_high_db} to {pass_band_low_db}  STOP_BAND_Thresholds={stop_band_high_db} to {stop_band_low_db}')
        return good

    def return_pass_band_stop_band_frequencies_db(self):
        return self.pass_band_stop_band_frequencies_db



class Spacex(object):
    def read_all_sp2_files(self, file_name):
        with open(file_name, "r") as f:
            lines = f.readlines()
            lines = [string.strip() for string in lines]
        return sorted(list(set(lines)))

    def __init__(self):
        self.pass_band_high_db_threshold = 0
        self.pass_band_low_db_threshold = -20

        self.stop_band_high_db_threshold = -30
        # A abnormally very low low_db
        self.stop_band_low_db_threshold = -200
        filters_processed = 0

        # Read the filenames of all sp2 files to be analyzed
        all_s2p_files = self.read_all_sp2_files("all_s2p_files")
        # Create a list of all s2p objects
        self.all_s2p_objects = []
        for s2p_file in all_s2p_files:
            self.all_s2p_objects.append(S2p(s2p_file))
            filters_processed += 1

        # Find yield for few db thresholds
        yields = defaultdict(list)
        for pass_band_low_db_threshold_increment in range(20):
            for stop_band_high_db_threshold_increment in range(20):
                good_all_band_filters = 0
                low_db_threshold_pass_band = self.pass_band_low_db_threshold - pass_band_low_db_threshold_increment
                high_db_threshold_stop_band = self.stop_band_high_db_threshold - stop_band_high_db_threshold_increment
                for s2p_object in self.all_s2p_objects:
                    good_all_band_filters += s2p_object.is_filter_good(low_db_threshold_pass_band,
                                                                       self.pass_band_high_db_threshold,
                                                                       self.stop_band_low_db_threshold,
                                                                       high_db_threshold_stop_band)
                yield_one = 100 * good_all_band_filters / filters_processed
                yield_str = (f'Yield in PASS_BAND_Thresholds = {self.pass_band_high_db_threshold} to '
                             f'{low_db_threshold_pass_band}  STOP_BAND_Thresholds={high_db_threshold_stop_band} to '
                             f'{self.stop_band_low_db_threshold};  Number of filters processed={filters_processed} '
                             f'good_filters={good_all_band_filters} Yield=', yield_one)
                yields[yield_one].append(yield_str)
        # Print the yields
        print(yields)
        # exit()
        for key in sorted(yields.keys()):
            print(f'Yield={key} ')
            for each_range in yields[key]:
                print(f'             {each_range}')
            print('\n\n')
        print('\n\n\n')
        # Plot the frequencies
        self.plot_frequencies_db_for_all_filters()

    def plot_frequencies_db_for_all_filters(self):
        # Plot frequency-db of all filters to identify outliers
        self.pass_band_stop_band_frequencies_db_for_all_filters = list()
        for s2p_object in self.all_s2p_objects:
            pass_band_stop_band_frequencies_db = s2p_object.return_pass_band_stop_band_frequencies_db()
            for freq, db in pass_band_stop_band_frequencies_db.items():
                self.pass_band_stop_band_frequencies_db_for_all_filters.append((freq, db))
        # Remove duplicate entries and print
        x_axis = list()
        y_axis = list()
        for freq_db in sorted(list(set(self.pass_band_stop_band_frequencies_db_for_all_filters))):
            x_axis.append(freq_db[0])
            y_axis.append(freq_db[1])
        x_np = np.array(x_axis)
        y_np = np.array(y_axis)
        plt.scatter(x_np, y_np)
        plt.savefig('all.png')
        plt.show()


if __name__ == "__main__":
    x = Spacex()
