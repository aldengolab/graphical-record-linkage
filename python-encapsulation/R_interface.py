# Python interface for R ebLink package
# Alden Golab
# 7-29-2016

# This code provides an interface for running ebLink through Python.

import os
import rpy2.robjects as ro
import rpy2.robjects as ro
import rpy2.robjects.packages as rpackages
from rpy2.robjects.packages import importr
from rpy2.robjects.vectors import StrVector, IntVector
from rpy2.robjects import pandas2ri
import numpy as np

STEEPNESS = 1

def run_eblink(tmp, tmp_dir, column_types, a, b, iterations, filenum, numrecords):
    '''
    Provides an interface with R to run ebLink in the background through R.
    '''
    pandas2ri.activate()
    # Get base packages
    # Import data to link
    data = ro.r('read.csv(file = "{}", header = T)'.format(tmp))
    # Set necessary variables
    ## X.c contains the categorical variables
    ## X.s contains the string variables
    ## p.c is the number of categorical variables
    ## p.s contains the number of string variables
    matrix = ro.r['as.matrix']
    c_cols = [x for x in column_types if column_types[x] == 'C']
    xc = matrix(data[c_cols])
    s_cols = [x for x in column_types if column_types[x] == 'S']
    xs = matrix(data[s_cols])
    pc = ro.IntVector([len(filter(lambda x: x == 'C', column_types.values()))])
    ps = ro.IntVector([len(filter(lambda x: x == 'S', column_types.values()))])
    # Number of iterations
    g = ro.IntVector([iterations])
    # Number of entries in file
    m = ro.IntVector([numrecords])
    # File number identifier
    fn = ro.IntVector(filenum)
    # Subjective choices for distortion probability prior
    a = ro.IntVector([a])
    b = ro.IntVector([b])
    # Steepness parameter; pre-set to recommended
    c = ro.IntVector([STEEPNESS])
    # Edit distance function; can be swapped for others if desired
    ro.r("d <- function(string1,string2){adist(string1,string2)}")
    d = ro.r['d']
    # If you have cloned the repo, this should be where the R code is located
    eb_pack = ro.r("source('../ebLink-master/R/code/ebGibbsSampler.R', chdir = TRUE)")
    plyr = importr("plyr")
    # Move to tmp directory to save results file
    os.chdir(tmp_dir)
    print 'Running the data linkage process...'
    # Runs the gibbs sampler
    gibbs = ro.r['rl.gibbs']
    lam = gibbs(file_num = fn, X_s = xs, X_c=xc, num_gs=g, a=a, b=b, c=c, d=d, M=m)
    os.chdir('..')
    # ro.r("lam.gs <- rl.gibbs(file.num=file.num,X.s=X.s,X.c=X.c,num.gs=10,a=a,b=b,c=c,d=d, M={})".format(iterations))
    appl = ro.r['apply']
    ro.r("len_uniq <- function(x){length(unique(x))}")
    len_uniq = ro.r['len_uniq']
    estPopSize = ro.r(appl(lam, 1, len_uniq))
    return np.array(lam)
