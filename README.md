# ebLink for Python
A python encapsulation of the R graphical record linkage algorithm used in [Steorts, et. al. (2015)](https://arxiv.org/abs/1312.4645).

The algorithm developed by Steorts in R can be found [here](https://github.com/resteorts/ebLink). This package is an adaptation for use with Python and is free, distributed under a Creative Commons Zero v1.0 Universal license.

If using this code, please follow Steorts' request to credit her work. Please also credit this repo.  

This code was created on behalf of the [University of Chicago Urban Labs](https://urbanlabs.uchicago.edu/).

## How To Use

The wrapper contained in `python-encapsulation` is meant to help the user format inputs easily into the underlying R process. This can be called interactively or non-ineractively.

If called interactively, the user will be presented with a series of prompts that asks for each input. Datasets to be linked must be in a supported format. Currently, this is csv files, pandas objects, and petl objects.

To call the class interactively, use:

`link = eblink.EBLink(interactive=True)`

If called non-interactively, the user must provide the necessary inputs.

+ `files` - a list of filenames to be loaded
+ `columns` - a list of column names to use for linking from the first file
+ `match_columns` - a dictionary that maps ``{first_file_column_name: [second_file_col_name, ..., k_file_col_name]}`` for all columns
+ `indices` - a list of column names corresponding to the unique ID/index for each file, in order
+ `column_types` - a dictionary mapping each column in `columns` to its type, either `s` for string or `c` for categorical
+ `iterations` - the number of gibbs samples to execute
+ `alpha` - the alpha of the prior Beta distribution
+ `beta` - the beta of the prior Beta distribution

#### Choosing Subjective Priors (Alpha and Beta)

## Bibliography

1. Steorts, Rebecca C., Rob Hall, and Stephen E. Fienberg. "Entity Resolution with Emprically Motivated Priors." *Bayesian Analysis*, v. 10, no. 4 (2015): 849-975.
