# Python interface for R ebLink package
# Alden Golab
# 7-29-2016

# This code provides an interface for running ebLink through Python.
# ebLink was developed in Steorts, et. al. 2015. R code is directly adapated
# from their repository:

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
    c_cols = [x for x in column_types if column_types[x].upper() == 'C']
    xc = matrix(data[c_cols])
    s_cols = [x for x in column_types if column_types[x].upper() == 'S']
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
    # Steepness parameter; pre-set to recommended value
    c = ro.IntVector([STEEPNESS])
    # Edit distance function; can be swapped for others if desired
    ro.r("d <- function(string1,string2){adist(string1,string2)}")
    d = ro.r['d']
    # Loads in Gibbs sampler and plyr packages
    eb_pack = ro.r("source('{}', chdir = TRUE)".format(find('ebGibbsSampler.R', '../../')))
    plyr = importr("plyr")
    # Move to tmp directory to save results file
    os.chdir(tmp_dir)
    print 'Running the gibbs sampler...'
    # Runs the gibbs sampler
    gibbs = ro.r['rl.gibbs']
    lam = gibbs(file_num = fn, X_s = xs, X_c=xc, num_gs=g, a=a, b=b, c=c, d=d, M=m)
    os.chdir('..')
    # Calculate estimated population sizes by finding number of uniques
    appl = ro.r['apply']
    ro.r("len_uniq <- function(x){length(unique(x))}")
    len_uniq = ro.r['len_uniq']
    estPopSize = appl(lam, 1, len_uniq)

    return np.array(lam), np.array(estPopSize)

def calc_linkages(linkage):
    '''
    Finds Maximal Matching Sets (MMS) based on a single linkage structure.
    Linkage should be a numpy array resulting from calling the ebLink code.

    Returns pairs of entries that have been matched using their entry number
    in the tmp file.
    '''
    pandas2ri.activate()
    link_pack = ro.r("source('{}', chdir = TRUE)".format(find('analyzeGibbs.R', '.')))
    links = ro.r['links']
    matrix = ro.r['as.matrix']
    linkage = matrix(linkage)
    est_links = links(linkage)
    pairwise = ro.r['pairwise']
    pairs = pairwise(est_links)
    return np.array(pairs)

def find(name, path):
    '''
    Looks for a file name in a given path.
    '''
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)
