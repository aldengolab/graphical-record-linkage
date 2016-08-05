library("RecordLinkage")
library("plyr")
# Load in the package with synthetic German data
data(RLdata500)

# Function to trim leading and trailing whitespace
trim <- function(string){gsub("^\\s+|\\s+$", "",string)}

# Record data for categorical fields
# Note 1: The data needs to be laid out with each row representing
# a record and each column representing a field.
# Note 2: The different files need to be "stacked" on top of each other.
X.c <- RLdata500[c("by","bm","bd")]
X.c <- as.matrix(RLdata500[,"bd"],ncol=1)
p.c <- ncol(X.c)
X.s <- as.matrix(RLdata500[-c(2,4,7)])
p.s <- ncol(X.s)

##### CODE TO SPLIT SINGLE LIST INTO THREE LISTS  #####

# File number identifier
# Note: Recall that X.c and X.s include all files "stacked" on top of each other.
# The vector below keeps track of which rows of X.c and X.s are in which files.
file.num <- rep(c(1,2,3),c(200,150,150))

##### MODELING CHOICES #####

# Subjective choices for distortion probability prior
a <-1
b <- 999

# String metric function (can be changed later)
# adist computes the Edit distance between string1 and string2
d <- function(string1,string2){adist(string1,string2)}

# Run Jaro-Winkler on all combinations of strings from first argument vs. second
# thus works like adist()
#outer_jarowinkler <- function(string1,string2) { outer(string1, string2, jarowinkler) }

# Comment out next line to use edit distance rather than JW
#d <- outer_jarowinkler

# ATTN: creates an issue if treating dates as string


# ##here is a simple distance metric that takes in r1 and r2
# ##i have a new version defined but will have to pull it off my machine

# # Define distance metric between pairs of records
  # # Presumes records consist of a first name, a last name, and a year
  # # Use Jaro-Winkler distance on names
  # # Add them all indiscriminately for now
# name_year_distance <- function(r1,r2){
	# require(RecordLinkage) # make sure jarowinkler is available
	# # Presumes that the format of a record is [first name, last name, year]
	  # # Double braces are needed for r[[]] since r1 and r2 are lists. The first
	  # #brace extracts a shorter list of size 1; the second brace extracts the
	  # #content of the list (the actual field).
	# d <- (1-jarowinkler(as.character(r1[[1]]),as.character(r2[[1]])))
	     # +(1-jarowinkler(as.character(r1[[2]]),as.character(r2[[2]])))
	     # +abs(r1[[3]]-r2[[3]])
	# return(d)
# }

# # Test record distance metric
# test.name_year_distance <- function() {
	# # Should give distance zero on identical records
	# stopifnot(name_year_distance(minidata[1,],minidata[1,])==0)
	# # Should give positive distance for some distinct records
	# stopifnot(name_year_distance(minidata[1,],minidata[3,])>0)
	# # Declare victory when all tests are passed
	# return(TRUE)
# }

# "Steepness" for string distortion distribution
c <- 1

