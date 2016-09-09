# Alden Golab
# 7/27/2016

# This file is an encapsulation in Python for ebLink, which runs in R.
# This program requires R to run.
# ebLink is drawn from Steorts, et. al. 2015 can can be found here:
#    https://github.com/resteorts/ebLink

## NOTES ##
# Current build only takes csvs. To add additional file types or connections,
#    please look at read_iterator.

from datetime import datetime
import rpy2
import pandas as pd
import os
import random
import subprocess
import csv
# Execute necessary dependencies for rpy2
from numpy import *
import scipy as sp
from pandas import *
import pickle

class EBlink(object):

    def __init__(self, interactive=False, files=[]):
        ## File locations & directories
        self._files = files # A list of filepaths or, possibly, python objects
        self._tmp_dir = None # Directory where temp files are stored
        self._tmp = None # Temporary csv for use in link
        self._crosswalk_file = None # File where crosswalk is saved
        self._interactive = interactive # Whether this will be run interactively
        ## Inputs
        self._columns = [] # Contains columns to use from first file
        self._indices = {} # Specifies UID columns for each file
        self._matchcolumns = {} # Contains lists mapping columns in other files to self._columns
        self._column_types = {} # Maps first file's columns to String or Categorical
        ## Subjective inputs
        self.alpha = None # Alpha value for prior
        self.beta = None # Beta value for prior
        self.iterations = 0 # Number of gibbs iterations to run
        ## Constructed inputs
        self._numrecords = 0 # Number of records
        self._filenum = [] # Labels each entry in joined CSV with file number from self._files
        ## Outputs from ebLink
        self.pop_est = 0 # De-duplicated/linked population estimated by ebLink
        self.pairs = None # Pairs linked by ebLink
        self.crosswalk = None # Crosswalk of UIDs
        self._lookup_pairs = {} # Create a dict to look-up pairs of entries
        ## Interactive mode
        if self._interactive == True:
            self._run_interactively()

    def _run_interactively(self):
        if self.files==[]:
            self.set_files()
        self.set_columns()
        self.get_col_types()
        self.betauild()
        self.define()
        self.model()
        self.betauild_crosswalk()
        self.pickle()

    ########################################################
    ################## Attribute Methods ###################
    ########################################################

    @property
    def files(self):
        return self._files

    @files.setter
    def files(self, files):
        if type(files) == list and len(filter(lambda x: os.path.isfile(x), files)) == len(files):
            self._files = files
        else:
            raise TypeError('Filename(s) input poorly formatted.')

    @property
    def columns(self):
        return self._columns

    @columns.setter
    def columns(self, columns):
        if type(columns) == list:
            self._columns = columns
        else:
            raise TypeError('Columns input poorly formatted.')

    @property
    def column_types(self):
        return self._column_types

    @column_types.setter
    def column_types(self, types):
        if type(types) == dict:
            self._column_types = types
        else:
            raise TypeError('Column types input poorly formatted.')

    @property
    def match_columns(self):
        return self._matchcolumns

    @match_columns.setter
    def match_columns(self, match_columns):
        if type(match_columns) == dict:
            if self._columns != None:
                for x in match_columns.keys():
                    if x not in self._columns[0]:
                        print '{} not in columns'.format(x)
                        raise NameError('match_columns keys do not match columns')
                self._matchcolumns = match_columns
            else:
                self._matchcolumns = match_columns
        else:
            raise TypeError('Match columns input poorly formatted.')

    @property
    def indices(self):
        return self._indices

    @indices.setter
    def indices(self, indices):
        if type(indices) == list:
            self._indices = indices
        else:
            raise TypeError('Indices input poorly formatted.')

    ########################################################
    ##################   Class Methods   ###################
    ########################################################

    def set_files(self, filename=None, delete=False):
        '''
        Sets the files to use for linkage. Takes a list of filepaths or a single
        filepath. All files must have headers.
        '''
        if delete: # This is for a redo function
            self._files = []
            print 'Files: {}'.format(self._files)
            return

        if self._interactive:
            print '\nPLEASE SPECIFY THE FILEPATHS FOR THE DATA YOU WISH TO LINK. Separate each filepath by a comma.\n'
            print 'Current files loaded: {}'.format(self._files)
            inp = None
            while inp == None:
                inp = raw_input('\nFilepaths: ')
            filename = []
            for x in inp.split(','):
                filename.append(x.strip())

        if type(filename) == list and len(filename) > 1:
            for n in filename:
                if os.path.isfile(n):
                    self._files.append(n)
                else:
                    print '\nERROR: {} is not a file.\n'.format(n)
                    self.file_retry()
        else:
            if type(filename) == list:
                filename = filename[0]
            if os.path.isfile(filename):
                self._files.append(filename)
            else:
                print '\nERROR: {} is not a file.\n'.format(filename)
                self.file_retry()

        if self._interactive:
            if not self.check_correct():
                self.set_files()

    def check_correct(self):
        '''
        Asks the user if they want to continue.
        '''
        answer = ''
        while answer.strip().upper() != 'Y' and answer.strip().upper() != 'N':
            answer = raw_input('\nARE THESE SETTINGS CORRECT (Y/N)? ')
        if answer.upper().strip() == 'N':
            return False
        else:
            return True

    def file_retry(self):
        '''
        Asks user if they'd like to retry in the event they enter a poorly
        formed filename.
        '''
        retry = None
        while retry == None:
            retry = raw_input('\nWould you like to retry? (Y/N): ')
        if retry == 'Y' or retry == 'y':
            self.set_files()
        else:
            return

    def set_columns(self, count=None, cols=[]):
        '''
        Will take a list containing the columns to be matched for each file,
        treating corresponding indices as matching. For example, an input of
        [['name', 'dob'], ['NAME', 'DOB']] will match (name, NAME) and
        (dob, DOB), where the first column comes from file 1 and the second from
        file 2.

        Yields a dict of {file1_column: [file2column,...,fileNcolumn]}.
        '''
        if self._interactive == True:
            if count == None:
                count = 1
            for f in self._files:
                print '\nPLEASE INDICATE WHICH COLUMNS IN {} YOU WOULD LIKE TO USE FOR LINKING. Separate each column name with a comma.'.format(f)
                cols = []
                to_add = None
                while to_add == None:
                    to_add = raw_input('\nColumns: ')
                for x in to_add.split(','):
                    cols.append(x.strip())
                self._columns.append(cols)
                if count > 1:
                    for x in self._columns[0]:
                        print '\nWhich column in this file matches to {}?'.format(x)
                        match = None
                        while match == None:
                            match = raw_input('\nColumn: ')
                        if x not in self._matchcolumns:
                            self._matchcolumns[x] = []
                        self._matchcolumns[x].append(match.strip())
                self.check_index(count)
                count += 1

            if not self.check_correct():
                self.set_columns(count)

        else:
            for i in range(len(cols[0])):
                if cols[0][i] not in self._matchcolumns:
                    self._matchcolumns[cols[0][i]] = []
                for l in cols[1:]:
                    self._matchcolumns[cols[0][i]].append(l[i])

    def check_index(self, num):
        '''
        Asks for an unique ID for a given file.
        '''
        answer = None
        while answer == None:
            answer = raw_input('\nDoes this file have a unique ID (Y/N)? ')
        if answer.strip().upper() == 'Y':
            index = None
            while index == None:
                index = raw_input('\nPlease specify the unique ID: ')
            self._indices[num] = index
        else:
            self._indices[num] = False
        return

    def get_col_types(self):
        '''
        Interactively asks user for types of each column.
        '''
        types = {}
        for col in self._columns[0]:
            typ = None
            while typ != 'C' and typ != 'S' and typ != 'c' and typ != 's':
                typ = raw_input('\nIs {} a categorical (C) or string (S) field?: '.format(col))
                if typ != 'C' and typ != 'S' and typ != 'c' and typ != 's':
                    print '\nERROR: Please enter C for categorical or S for string.'
            types[col] = typ.upper()

        if not self.check_correct():
            self.get_col_types()
        else:
            self._column_types = types

    def define(self, a=None, b=None, interations=0):
        '''
        Asks user to define alpha and beta for prior distribution or allows
        coder to set if non-interactive session.
        '''
        if self._interactive == True:
            print '\nPLEASE SET THE ALPHA AND BETA VALUES FOR THE PRIOR DISTRIBUTION.'
            print 'If you are unsure how to set these values, please see the documentation for ebLink.\n'
            self.alpha = None
            while self.alpha == None:
                self.alpha = raw_input('Alpha: ')
            self.beta = None
            while self.beta == None:
                self.beta = raw_input('Beta: ')
            print '\nHOW MANY INTERATIONS SHOULD BE RUN? RECOMMENDED > 100,000.'
            self.iterations = 0
            while self.iterations == 0:
                self.iterations = raw_input('\nIterations: ')
            if not self.check_correct():
                self.define()

        else:
            self.alpha = a
            self.beta = b
            self.iterations = iterations

    def build(self, headers=False):
        '''
        Builds the inputs for ebLink. Constructs filenum input as well as
        a single hidden tmp csv for feeding into the system.
        '''
        if len(self._files) < 2:
            print 'Only one file found. Please set additional files.'
            return

        self._build_directory()
        columns = self._columns[0] + ['ETL_ID'] # Adding a temporary ID

        with open(self._tmp, 'w') as dest:
            wtr = csv.writer(dest)
            file_count = 1
            # Go through each file
            for f in self._files:
                rdr, fi = self.read_iterator(f)
                headers = rdr.next()
                # In case iterator returns tuples instead of lists
                if type(headers) == tuple:
                    headers = list(headers)
                if file_count == 1:
                    wtr.writerow(columns)
                # For each line in that file
                for line in rdr:
                    # In case iterator returns tuples instead of lists
                    if type(line) == tuple:
                        line = list(line)
                    # Count records
                    self._numrecords += 1
                    # Add file number to column to be fed into ebLink
                    self._filenum.append(file_count)
                    if file_count == 1:
                        row = []
                        for col in self._columns[0]:
                            index = headers.index(col)
                            row.append(line[index])
                    elif file_count >= 2:
                    # Else use match_columns to make sure columns are matched to
                    # first file's columns in the new file.
                        row = []
                        for col in self._columns[0]:
                            index = headers.index(self._matchcolumns[col][file_count-2])
                            row.append(line[index])
                    # Add additional ID, unique for the link
                    row.append(self._numrecords)
                    wtr.writerow(row)
                if fi:
                    fi.close()
                file_count += 1

    def read_iterator(self, filepath):
        '''
        Takes a filepath and returns an iterator. Iterator returns each line as
        a list of elements, much like csv writer. Must return headers as first
        line. Should pass back two values, first is iterator, second is file
        instance (can be None).

        All returned iterators must work with both .next() and for loops. Can
        return tuples or lists, where each column is a separate tuple or list
        entry.

        **ADD NEW CONNECTIONS/FILE TYPES HERE**
        '''
        ### CSV ###
        if 'csv' in filepath:
            f = open(filepath, 'r')
            reader = csv.reader(f)
            return (reader, f)

        ### petl functionality for use with Urban ETL ###
        if 'petl' in str(type(filepath)):
            return (iter(filepath), None)

        ### Error Message ###
        else:
            raise NameError('This file type or connection is not yet supported.')

    def _build_directory(self):
        '''
        Private function to build a temporary directory for storing data.
        '''
        self._tmp_dir = '._tmp-{}'.format(random.randint(0, 10000))
        bashCommand = 'mkdir {}'.format(self._tmp_dir)
        output = subprocess.check_output(['bash','-c', bashCommand])
        now = datetime.today().strftime('%y%m%d-%H%M%S')
        self._tmp = '{}/{}-{:.2}.csv'.format(self._tmp_dir, now, random.random())

    def model(self):
        '''
        Carries out modeling in R. Returns a numpy array
        '''
        import R_interface as ri
        result, estPopSize = ri.run_eblink(self._tmp, self._tmp_dir,
         self.column_types, self.alpha, self.beta, self.iterations, self._filenum,
         self._numrecords)
        self.pop_est = np.average(estPopSize)
        del estPopSize
        print "Estimated population size: ", self.pop_est
        print "Total number of records: ", self._numrecords
        if self.pop_est <= self._numrecords - 1:
            # Only look for linked pairs if there are pairs to look for
            p = ri.calc_linkages(result)
            self.pairs = [tuple(x) for x in p]
        del result

    def build_crosswalk(self):
        '''
        Writes identified links to a file using UIDs.

        ## This function uses Pandas and may need to be edited for scaling! ##
        '''
        if not self.pairs: # Don't run this if there aren't any pairs
            print 'No pairs identified.'
            return

        for pair in self.pairs:
            self._lookup_pairs = self._add_to_dict(self._lookup_pairs, pair[0], pair[1])
        rv = {} # This is the output data set
        new_id = 0 # This is a new, uninteresting id for building rv
        filenum_index = 0 # This is for indexing into the self.filenum object
        placed = {} # Memo

        # Go through each file and read through all the objects
        for i in range(len(self._files)):
            fp = self._files[i]
            rdr, fi = self.read_iterator(fp)
            headers = list(rdr.next()) # Get headers for this file
            unique = self._indices[i] # Grab UID name this file from build
            uni_index = headers.index(unique) # Get the index for the UID within this file

            for line in rdr:
                line = list(line)
                # Check that file and filenum specified align
                if self._filenum[filenum_index] != (i + 1):
                    print "WARNING: File numbers don't match for entry {}.".format(filenum_index)
                    print 'Listed file {} should be {}.'.format(self._filenum[filenum_index], i + 1)
                    print 'Aborting. Check inputs for mismatch.'
                    print 'Index with error: ', filenum_index
                    print self._filenum[filenum_index + 1], ' is next.'
                    print 'Filenum: ', self._filenum
                    return

                # Check if this entry has matches that are already placed
                placed_matches = []
                if filenum_index in self._lookup_pairs:
                    placed_matches = [x for x in self._lookup_pairs[filenum_index] if x in placed]

                if len(placed_matches) > 0:
                    # If so, then add this UID to that entry
                    match_index = placed[placed_matches[0]]
                    # If there's already an entry in this column, it means that
                    # ebLink has detected a duplicate within the data file.
                    # This will be recorded as a tuple, but can be ignored
                    # later.
                    if rv[match_index][i] != '':
                        old = rv[match_index][i]
                        rv[match_index][i] = (old, line[uni_index])
                    # Otherwise just add the new UID
                    else:
                        rv[match_index][i] = line[uni_index]
                    placed[filenum_index] = match_index
                    filenum_index += 1
                else:
                    # Else add the unique id from original file for a new id
                    rv[new_id] = ['' for y in range(len(self._files))]
                    rv[new_id][i] = line[uni_index]
                    placed[filenum_index] = new_id
                    new_id += 1
                    filenum_index += 1
            if fi:
                fi.close()

        # Place crosswalk into attributes as a Pandas Dataframe
        self.crosswalk = pd.DataFrame.from_dict(rv, orient='index')

    def build_linked_data(self, interactive=False):
        '''
        Builds a set of linked data.
        '''
        rv = []
        data = pd.read_csv(self._tmp)
        keeps = [x[0] for x in self.pairs] # Entries to keep
        deletes = [y for sub in [x[1:] for x in self.pairs] for y in sub] # Flattens list of others

        rv.append(self._columns[0] + ['ETL_ID'])
        for i in range(len(self._filenum)):
            if interactive and (i+1 in keeps or i+1 in deletes):
                print 'Linked entries:'
                print '  Entry {}: {}'.format(i+1, list(data.iloc[i]))
                for j in self._lookup_pairs[i]:
                    print '  Entry {}: {}'.format(j, list(data.iloc[j]))
                keep = None
                while keep not in self._lookup_pairs[i]:
                    keep = int(raw_input('Please select which ETL_ID to keep: '))
                keep = int(keep.strip())- 1
                rv.append(list(data.iloc[keep]))
            elif i+1 not in deletes:
                rv.append(list(data.iloc[i]))

        self.linked_set = pd.DataFrame(rv)

    def _add_to_dict(self, dict, value1, value2):
        '''
        Adds both values and redundantly refers them to one another in dict.
        '''
        if value1 not in dict:
            dict[value1] = [value2]
        elif value1 in dict:
            dict[value1].append(value2)
        if value2 not in dict:
            dict[value2] = [value1]
        elif value2 in dict:
            dict[value2].append(value1)
        return dict

    def pickle(self, filename=None):
        '''
        Pickles this model & settings for later use.
        '''
        if filename == None:
            filename = 'eblink_' + datetime.today().strftime('%y%m%d-%H%M%S') + '.pkl'
        f = open(filename, 'w')
        pickle.dump(self, f)
        f.close()
        return True

    def write(self, obj, filename):
        '''
        Writes ebLink object to file.
        '''
        if filename == None:
            filename = 'links_' + datetime.today().strftime('%y%m%d-%H%M%S') + '.ebout'
        try:
            pd.to_csv(obj, filename)
        except:
            try:
                pd.to_csv(pd.DataFrame(obj), filename)
            except:
                with open(filename, w) as f:
                    f.write(obj)

    def clean_tmp(self):
        '''
        Deletes the tmp folder.
        '''
        subprocess.call('rm -r {}'.format(self._tmp_dir), shell=True)
        print 'Temp folder deleted.'
