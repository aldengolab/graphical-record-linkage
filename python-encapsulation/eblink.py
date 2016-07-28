# Alden Golab
# 7/27/2016

# This file is an encapsulation in Python for ebLink, which runs in R.

import datetime
import rpy2
import pandas as pd
import os
import random
# Execute necessary dependencies for rpy2
from numpy import *
import scipy as sp
from pandas import *
from rpy2.robjects.packages import importr
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
pandas2ri.activate()

class EBlink:

    def __init__(self, interactive=False):
        self._files = []
        self._headers = []
        self._columns = []
        self._matchcolumns = []
        self._column_types = {} # Maps first file's columns to Cat or Num
        self._a = None
        self._b = None
        self._filenum = None
        self.tmp_dir = None
        self.tmp = None
        self._interactive = interactive
        if self._interactive == True:
            self._run_interactively()

    def _run_interactively(self):
        self.set_files()
        self.set_columns()
        self.get_col_types()
        self.build()
        self.define()
        self.model()
        self.write_result()

    @property
    def column_types(self):
        return self._column_types

    @column_types.setter
    def column_types(self, types):
        self._column_types = types

    @property
    def files(self):
        return self._files

    @property
    def columns(self):
        return self._columns

    def set_files(self, filename=None, delete=False):
        '''
        Sets the files to use for linkage. Takes a list of filepaths or a single
        filepath. All files must have headers.
        '''
        if delete:
            self._files = []
            print 'Files: %s'.format(self._files)
            return

        if self._interactive == True:
            print 'Please specify the filepaths for the data you wish to link.'
            print 'Separate each filepath by a comma.'
            inp = None
            while inp == None:
                inp = raw_input('Filepaths: ')
            filename = []
            for x in inp.split(','):
                filename.append(x.strip())

        if type(filename) == list and len(filename) > 1:
            for n in filename:
                if os.isfile(n):
                    self._files.append(n)
                else:
                    print '{} is not a file.'.format(n)
        else:
            if type(filename) == list:
                filename = filename[0]
            if os.isfile(filename):
                self._files.append(filename)
            else:
                print '{} is not a file.'.format(filename)

    def set_columns(self, cols=[]):
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
            count = 0
            for f in self._files:
                print 'Please indicate which columns in {} you would like to use for matching.'.format(f)
                print 'Separate each column name with a comma.'
                cols = []
                to_add = None
                while to_add == None:
                    to_add = raw_input('Columns: ')
                for x in to_add.split(','):
                    cols.append(x.strip())
                self._columns.append(cols)
            if count > 1:
                for x in self._columns[0]:
                    print 'Which column in this file matches to {}?'.format(x)
                    match = None
                    while match == None:
                        match = raw_input('Column: ')
                    if x not in self._matchcolumns:
                        self._matchcolumns[x] = []
                    self._matchcolumns[x].append(match.strip())
            count += 1
        else:
            for i in range(len(cols[0])):
                if cols[0][i] not in self._matchcolumns:
                    self._matchcolumns[cols[0][i]] = []
                for l in cols[1:]:
                    self._matchcolumns[cols[0][i]].append(l[i])

    def get_col_types(self):
        '''
        Interactively asks user for types of each column.
        '''
        types = {}
        for col in self._columns[0]:
            typ = None
            while typ == None:
                typ = raw_input('Is {} a categorical (C) or numerical (N) field?: '.format(col))
            types[col] = typ
        self.columns = types

    def define(self, a=None, b=None):
        '''
        Asks user to define alpha and beta for prior distribution or allows
        coder to set if non-interactive session.
        '''
        if self._interactive == True:
            print 'Please set the alpha and beta values for the prior distribution.'
            print 'If you are unsure how to set these values, please see the documentation for ebLink.'
            while self._a == None:
                self._a = raw_input('Alpha: ')
            while self._b == None:
                self._b = raw_input('Beta: ')
        else:
            self._a = a
            self._b = b

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

        with open(self.tmp, 'w') as dest:
            wtr = csv.writer(dest)
            file_count = 1
            # Go through each file
            for file in files:
                rdr = self.read_iterator(file)
                headers = rdr.next()
                # For each line in that file
                for line in rdr:
                    # Add file number to column to be fed into ebLink
                    self._filenum.append(file_count)
                    # If first file, columns are sorted correctly
                    if file_count == 1:
                        row = line
                    # Else use match_columns to make sure columns are matched to
                    # first file's columns in the new file.
                    else:
                        row = []
                        for col in columns:
                            index = list.index(self._matchcolumns[col][file_count-2])
                            row.append(list[index])
                    wtr.writerow(row)

    def read_iterator(self, filepath):
        '''
        Takes a filepath and returns an iterator. Iterator returns each line as
        a list of elements, much like csv writer. Must return headers as first
        line.

        **ADD NEW CONNECTIONS/FILE TYPES HERE**
        '''
        if 'csv' in file:
            f = open(f, 'r')
            reader = csv.reader(f)
            return reader
        else:
            raise NameError('This file type or connection is not yet supported.')

    def _build_directory(self):
        '''
        Private function to build a temporary directory for storing data.
        '''
        self.tmp_dir = '.tmp-{}'.format(random.randint(0, 100))
        bashCommand = 'mkdir {}'.format(self.tmp_dir)
        output = subprocess.check_output(['bash','-c', bashCommand])
        now = datetime.datetime.today().strftime('%y%m%d-%H:%M:%S')
        self.tmp = '{}/{}-{:.2}.csv'.format(self.tmp_dir, now, random.random())

    def model(self):
        '''
        Carries out modeling in R.
        '''
