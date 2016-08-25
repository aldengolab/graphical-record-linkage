# ebLink for Python

A python encapsulation of the R graphical record linkage algorithm from
[Steorts, et. al. (2015)](https://arxiv.org/abs/1312.4645).

The algorithm developed by Steorts in R can be found
[here](https://github.com/resteorts/ebLink). This package is an adaptation for
use with Python and is free, distributed under a Creative Commons Zero v1.0
Universal license.

If using this code, please follow Steorts' request to credit her work.
Please also credit this repo.  

This code was created on behalf of the
[University of Chicago Urban Labs](https://urbanlabs.uchicago.edu/) by
[Alden Golab](http://www.github.com/aldengolab).

## How To Use

The wrapper contained in `python-encapsulation` is meant to help the user
format inputs easily into the underlying R process. This can be called
interactively or non-interactively.

If called interactively, the user will be presented with a series of prompts
that asks for each input. Datasets to be linked must be in a supported format.
Currently, this are csv files, [pandas](http://pandas.pydata.org/) dataframes,
and [petl](petl.readthedocs.io) tables.

To call the class interactively, use:

`link = eblink.EBLink(interactive=True)`

If called non-interactively, the user must provide the necessary inputs.

+ `files` - a list of filenames to be loaded
+ `columns` - a list of column names to use for linking from the first file
+ `match_columns` - a dictionary that maps ``{first_file_column_name:
  [second_file_col_name, ..., k_file_col_name]}`` for all columns
+ `indices` - a list of column names corresponding to the unique ID/index for
  each file, in order
+ `column_types` - a dictionary mapping each column in `columns` to its type,
  either `s` for string or `c` for categorical
+ `iterations` - the number of gibbs samples to execute
+ `alpha` - the alpha parameter of the prior distortion probability distribution
+ `beta` - the beta parameter of the prior distortion probability distribution

#### Choosing Subjective Priors/Tuning Parameters (Alpha and Beta)

These are the alpha and beta shape parameters for the distortion probability
prior, which is a Beta distribution. This is one of the more complicated
aspects of the system that Steorts, et. al. acknowledge as an area for future
research.


## A Rough Sketch of the Method

Say we have two datasets that we are looking to link, A and B. Imagine, then,
that we have three lists of records: A, B, and a list of *latent individuals* C,
which can be linked to records in A or B, and represents the unique individuals
from both lists.

To begin, assign all records in A and all records in B to distinct records in C.
The algorithm selects two records at random and looks to see whether they are
assigned to the same record in C.

If they are assigned to the same record, the algorithm proposes splitting them
by assigning them to different records in C and re-sampling the distortion
probabilities for each field. A decision is made using the Metropolis choice
mechanism on whether to accept this proposal. [[See more on Metroplis-Hastings
MCMC Sampling]](https://en.wikipedia.org/wiki/Metropolis%E2%80%93Hastings_algorithm)

If they are not assigned to the same record, the algorithm proposes combining
them by assigning them to the same record in C, and the same process is carried
out.

Steorts, et. al. (2015) reference Jain & Neal (2004) when describing these
split-merge moves; for more detail, check out their article and dig into the
probability distributions detailed within Steorts, et. al (2015).

Once the linkage structure is determined, the method then makes a determination
as to which links to accept. Links are only accepted between two records, one
drawn from dataset A and the second from dataset B, if they are both linked to
the same latent individual in C as their *most likely link*. Steorts, et. al.
refer to this as the records' *maximal matching set* or MMS. Two records are
only linked if they share the same *most probable* MMS.

See Steorts, et. al. (2015) directly for more detail.

## Advantages

The graphical approach used by Steorts et. al. has some remarkable advantages:
+ **Efficiency at Scale**: Using a split/merge algorithm drawn from Jain & Neal (2004),
  *time efficiency is entirely dependent on the number of iterations selected*.
  In general, this number is subjectively selected to give you a good view of the
  network, with the larger number of iterations approaching the true population
  linkage. Max iterations is given by `n(n-1) / 2`, where `n` is the total
  number of observed records.
+ **No arbitrary cutoffs**: This method does not select an arbitrary cutoff for
  linkage probability (e.g. p > .90). Instead, linkages are made when two entries
  share a most probable maximal matching set (MMS).
+ **Transitivity Preservation**: The use of MMSs also has the added benefit
  of preserving transitivity. That is, if entry A links to entry B and entry B
  links to entry C, most linkage systems are not able to answer whether A ought
  to be linked to C (in fact, the p(A = C) might be different when directly
  calculated vs. p(A=B) * p(B=C)).
+ **Use of multiple files**: This method is able to take more than two files;
  in fact, there is no limit to the number of files it can take at once outside
  of memory errors.
+ **Elimination of Clerical Review**: ebLink does not require clerical review as
  it is entirely unsupervised and determination of linkage is not dependent on
  a simple probability of identity.
+ **Simultaneous Deduplication and Linkage**: ebLink is able to simultaneously
  link and deduplicate.

## Disadvantages

Nevertheless, it does have some drawbacks:
+ **Small Set Efficiency**: While a simple edit distance based linkage may
  operate in a matter of minutes on a dataset with less than 1,000 records;
  ebLink's time efficiency will still be a matter of iterations. Even with a
  set of 500 records, it is best to have 100,000 iterations.
+ **Low Dimensional Data**: ebLink performs on par with other systems for
  data linkage tasks between datasets with low dimensionality (i.e. few fields)
  when it comes to accuracy, however is able to handle more noise in the data.
  (Steorts et. al., 2015).

## Future Work

1. Determination of how to alter blocking -- this is not explicit in the Steorts,
et. al. (2015) documentation.
2. More direction on how to derive alpha and beta from the data.

## Bibliography

1. [Steorts, Rebecca C., Rob Hall, and Stephen E. Fienberg. 2015. "Entity Resolution
  with Emprically Motivated Priors." *Bayesian Analysis*, 10(4)):
  849-975.](https://arxiv.org/abs/1312.4645)
2. [Jain, Sonia and Radford M. Neal. 2004. "A Split-Merge Markov Chain Monte Carlo
  Procedure for the Dirichlet Process Mixture Model." *Journal of Computational
  and Graphical Statistics*, 13(1): 158-182.](http://www.jstor.org/stable/1391150)
3. [Sadinle, Mauricio. 2014. "Detecting Duplicates in a Homicide Registry Using a Bayesian Partitioning Approach." *The Annals of Applied Statistics*. 8(4): 2404.](http://arxiv.org/abs/1407.8219)
