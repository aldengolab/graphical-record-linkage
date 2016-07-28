# Alden Golab
# 7/27/2016

# This file is an encapsulation in Python for ebLink, which runs in R.
# This program requires R to run.

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

class EBlink(object):

    def __init__(self, interactive=False):
        self._files = []
        self._headers = []
        self._columns = []
        self._matchcolumns = {}
        self._column_types = {} # Maps first file's columns to Cat or Num
        self._a = None
        self._b = None
        self._iterations = 0
        self._filenum = []
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
        return
        self.model()
        self.write_result()

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
            answer = raw_input('\nARE THESE SETINGS CORRECT (Y/N)? ')
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
                count += 1
            if not self.check_correct():
                self.set_columns()
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
            while self._a == None:
                self._a = raw_input('Alpha: ')
            while self._b == None:
                self._b = raw_input('Beta: ')
            print '\nHOW MANY INTERATIONS SHOULD BE RUN? RECOMMENDED > 100,000.'
            while self._iterations == 0:
                self._iterations = raw_input('\nIterations: ')
            if not self.check_correct():
                self.define()

        else:
            self._a = a
            self._b = b
            self._iterations = iterations

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
            for f in self._files:
                rdr, fi = self.read_iterator(f)
                headers = rdr.next()
                if file_count == 1:
                    wtr.writerow(columns)
                # For each line in that file
                for line in rdr:
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
        self.tmp_dir = '.tmp-{}'.format(random.randint(0, 10000))
        bashCommand = 'mkdir {}'.format(self.tmp_dir)
        output = subprocess.check_output(['bash','-c', bashCommand])
        now = datetime.today().strftime('%y%m%d-%H:%M:%S')
        self.tmp = '{}/{}-{:.2}.csv'.format(self.tmp_dir, now, random.random())

    def model(self):
        '''
        Carries out modeling in R.
        '''
        # Wait to import R objects as it begins an R session and takes memory.
        import rpy2
        import rpy2.robjects as ro
        from rpy2.robjects.packages import importr, data
        from rpy2.robjects.vectors import DataFrame
        from rpy2.robjects import pandas2ri
        pandas2ri.activate()
        from rpy2.robjects.numpy2ri import numpy2ri
        ro.conversion.py2ri = numpy2ri
        rpy2.robjects.activate()

        r_base = importr('base')
        # Import data to link
        data = DataFrame.from_csvfile(self.tmp)
        # Set necessary variables
        ## X.c contains the categorical variables
        ## X.s contains the string variables
        ## p.c is the number of categorical variables
        ## p.s contains the number of string variables
        robjects.r("p.c <- {}".format(len(filter(lambda x: x == 'C', self.column_types.values()))))
        robjects.r("p.s <- {}".format(len(filter(lambda x: x == 'S', self.column_types.values()))))
        # If you have cloned the repo, this should be where the R code is located
        robjects.r("source('../ebLink-master/R/code/ebGibbsSampler.R', chdir = TRUE)")
        robjects.r("library(plyr)")
        # Runs the gibbs sampler
        print 'Running the data linkage process...'
        robjects.r("lam.gs <- rl.gibbs(file.num=file.num,X.s=X.s,X.c=X.c,num.gs=10,a=a,b=b,c=c,d=d, M={})".format(self._iterations))
