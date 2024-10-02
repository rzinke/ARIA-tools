
import os
import json
import pickle
from datetime import datetime
from shapely import from_wkt

from ARIAtools.util.shp import open_shp


class RunLog:
    """
    Record inputs and processing parameters.
    Use to recall which products, scenes have already been processed.
    """
    def __init__(self, workdir, verbose=None):
        """Initialize instance of the RunLog object.
        Record work directory and verbose T/F.
        Initialize logs dictionary if does not already exist.
        """
        self.workdir = workdir

        self.verbose = verbose

        if not hasattr(self, 'logs'):
            self.logs = {}

        # Construct file name
        self.file_name = os.path.join(self.workdir, 'RunLog.json')


    def load(self):
        """
        Recall log entries from pickle file.
        """
        if os.path.exists(self.file_name):
            with open(self.file_name, 'r') as log_file:
                self.logs = json.load(log_file)

            log_names = [*self.logs.keys()]
            log_names.sort(reverse=True)

            return log_names

        else:
            if self.verbose:
                print('No previous logs recorded.')

            return None

    def dump(self):
        """
        Record log entires to pickle file.
        """
        with open(self.file_name, 'w') as log_file:
            json.dump(self.logs, log_file)

    def write(self, atr_name, atr_value):
        """
        Assign attribute to log dict, and dump contents to file.

        Parameters
        atr_name - str, attribute name
        atr_value - [any], attribute value, can be any kind of object
        """
        # Write generic attribute to dictionary
        log_names = self.load()
        current_run = log_names[0]
        self.logs[current_run][atr_name] = atr_value

        # Special records for prods_TOTbbox and prods_TOTbbox_matadatalyr
        if atr_name in ['prods_TOTbbox', 'prods_TOTbbox_metadatalyr']:
            shp = open_shp(atr_value)
            self.logs[current_run][atr_name+'_poly'] = shp.wkt

        self.dump()

    def create_new_entry(self):
        """
        Begin a new log file with run name constructed from machine clock date
        and time.

        Parameters
        workdir - str, working directory for extract or TSsetup run
        """
        # Check if work directory exists
        os.makedirs(self.workdir, exist_ok=True)

        # Load previous runs
        if os.path.exists(self.file_name):
            self.load()

        # Initialize file with run date and time
        run = datetime.now().strftime('%Y%m%d-%H%M%S')
        log_names = self.logs[run] = {}
        self.dump()

        if self.verbose:
            print(f'Run log initialized. Run name: {run:s}')

    def get_current(self):
        """
        Retrieve the dictionary of the current log entry.
        """
        # Load all log entries
        log_names = self.load()

        # Retrieve current entry
        current_run = log_names[0]

        return self.logs[current_run]

    def get_previous(self):
        """
        Retrieve the dictionary of the current log entry.
        """
        # Load all log entries
        log_names = self.load()

        # Retrieve current entry
        previous_run = log_names[1]

        return self.logs[previous_run]

    def determine_rerun(self):
        """
        Compare the input arguments of the current run to those of the
        previous run. If they are the same, this could be considered a
        re-run of the previous.
        """
        # Pre-set rerun value
        rerun = False

        # Try loading existing args file
        log_names = self.load()
        if len(log_names) > 1:
            # Names of current and previous runs
            curr_log_name, prev_log_name = log_names[:2]

            # Retreive current and previous logs
            curr_log = self.logs[curr_log_name]
            prev_log = self.logs[prev_log_name]

            # Compare current arguments to previous
            if ('args' in curr_log.keys()) and ('args' in prev_log.keys()):
                curr_args = curr_log['args']
                prev_args = prev_log['args']
                if curr_args == prev_args:
                    rerun = True

            # Check bounding boxes
            if ('prods_TOTbbox_poly' in curr_log.keys()) \
                    and ('prods_TOTbbox_poly' in prev_log.keys()):
                curr_bbox = from_wkt(curr_log['prods_TOTbbox_poly'])
                prev_bbox = from_wkt(prev_log['prods_TOTbbox_poly'])
                rerun = True if curr_bbox == prev_bbox else False


        # Write re-run value to log
        self.write('rerun', rerun)

        if self.verbose:
            print(f"Re-run of previous: {rerun}")

        return rerun
