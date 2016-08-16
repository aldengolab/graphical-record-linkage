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

    def __init__(self, interactive=False):
        self._files = []
        self._headers = []
        self._columns = []
        self._indices = {}
        self._matchcolumns = {}
        self._column_types = {} # Maps first file's columns to Cat or Num
        self.a = None
        self.b = None
        self._numrecords = 0
        self.iterations = 0
        self._filenum = []
        self._tmp_dir = None
        self._tmp = None
        self._interactive = interactive
        self.pop_est = 0
        self.result = None
        self.pairs = None
        if self._interactive == True:
            self._run_interactively()

    def _run_interactively(self, files=True):
        if files==True:
            self.set_files()
        self.set_columns()
        self.get_col_types()
        self.build()
        self.define()
        self.model()
        return
        self.write_links()
        self.pickle()

    @property
    def files(self):
        return self._files

    @files.setter
    def files_setter(self, files):
        if type(files) == list and len(filter(lambda x: os.path.isfile(x), files)) == len(files):
            self._files = files
        else:
            raise NameError('Filename(s) poorly formed.')

    @property
    def columns(self):
        return self._columns

    @property
    def column_types(self):
        return self._column_types

    @column_types.setter
    def column_types_setter(self, types):
        if type(types) == dict:
            self._column_types = types
        else:
            raise NameError('Types must be dict.')

    def set_files(self, filename=None, delete=False):
        '''
        Sets the files to use for linkage. Takes a list of filepaths or a single
        filepath. All files must have headers.
        '''
        if delete:
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

        Otherwise, can run ly.
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
            self.a = None
            while self.a == None:
                self.a = raw_input('Alpha: ')
            self.b = None
            while self.b == None:
                self.b = raw_input('Beta: ')
            print '\nHOW MANY INTERATIONS SHOULD BE RUN? RECOMMENDED > 100,000.'
            self.iterations = 0
            while self.iterations == 0:
                self.iterations = raw_input('\nIterations: ')
            if not self.check_correct():
                self.define()

        else:
            self.a = a
            self.b = b
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
        columns = self._columns[0]

        with open(self._tmp, 'w') as dest:
            wtr = csv.writer(dest)
            file_count = 1
            # Go through each file
            for f in self._files:
                rdr, fi = self.read_iterator(f)
                headers = rdr.next()
                if file_count == 1:
                    wtr.writerow(columns)
                # For each line in that file
                for line in rdr:
                    # Count records
                    self._numrecords += 1
                    # Add file number to column to be fed into ebLink
                    self._filenum.append(file_count)
                    if file_count == 1:
                        row = []
                        for col in columns:
                            index = headers.index(col)
                            row.append(line[index])
                    elif file_count >= 2:
                    # Else use match_columns to make sure columns are matched to
                    # first file's columns in the new file.
                        row = []
                        for col in columns:
                            index = headers.index(self._matchcolumns[col][file_count-2])
                            row.append(line[index])
                    wtr.writerow(row)
                fi.close()
                file_count += 1

    def read_iterator(self, filepath):
        '''
        Takes a filepath and returns an iterator. Iterator returns each line as
        a list of elements, much like csv writer. Must return headers as first
        line. Should pass back two values, first is iterator, second is file
        instance (if necessary).

        **ADD NEW CONNECTIONS/FILE TYPES HERE**
        '''
        if 'csv' in filepath:
            f = open(filepath, 'r')
            reader = csv.reader(f)
            return (reader, f)
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
         self.column_types, self.a, self.b, self.iterations, self._filenum,
         self._numrecords)
        self.pop_est = np.average(estPopSize)
        del estPopSize
        p = ri.calc_linkages(result)
        self.pairs = [tuple(x) for x in p]
        del result

    def write_links(self, filename=None):
        '''
        Writes identified links to a file using UIDs.
        '''
        lookup_pairs = {x[0]:x[1] for x in link.pairs}
        lookup_pairs.update({x[1]:x[0] for x in link.pairs})
        all_dupes = lookup_pairs.values()

        newfile = 'crosswalk_' + datetime.today().strftime('%y%m%d-%H%M%S') + '.csv'
        deduped = {}

        new_id = 0
        filenum_index = 0
        for i in range(len(self._files)):
            fp = self._files[i]
            f = open(fp, 'r')
            rdr = csv.reader(f)
            headers = rdr.next()
            # Grab unique from indices private attribute
            unique = self._indices[i]
            # Get the index within this data file
            uni_index = headers.get_index(unique)
            for line in rdr:
                # Check that files align and that this entry isn't duplicated
                if self._filenum[filenum_index] != (i + 1):
                    print "WARNING: File numbers don't match."
                elif filenum_index not in all_dupes:
                    # Add the unique id from original file
                    deduped[new_id] = [line[uni_index]]
                    new_id += 1
                    filenum_index += 1
                elif filenum_index in all_dupes:
                    deduped_id = self._look_up(deduped, lookup_pairs[filenum_index])
                    if deduped_id:
                        deduped[deduped_id].append(line[uni_index])
                    else:
                        deduped[new_id] = [line[uni_index]]
                new_id += 1
                filenum_index += 1
            f.close()

        self.crosswalk = pd.DataFrame(deduped)

    def _look_up(self, deduped, i):
        '''
        Takes filenum_index and returns the matching key, if it is already
        in the deduped dict.
        '''
        if i in deduped.values():
            for k, v in deduped:
                if i in v:
                    return k
        else:
            return False

    def pickle(self, filename):
        '''
        Pickles this model & settings for later use.
        '''
        f = open(filename, 'w')
        pickle.dump(self, f)
        f.close()
        return True

    def write(self, obj, filename):
        '''
        Writes results of ebLink object to file.
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
