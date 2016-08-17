# This is the main Gibbs sampler in Steorts (2015), Bayesian Analysis.
#If you use this code, please cite Steorts (2015), "Entity Resolution with Emprically Motivated Priors", Bayesian Analysis, (10),4:849-975.

#ebLink Copyright 2015, 2016 Rebecca C. Steorts (beka@stat.duke.edu)

#ebLink is free software: you can redistribute it and/or modify it
#under the terms of the Creative Commons license, either version 3 of the license,
#or (at your option) any later version.

#ebLink is distributed in the hope it will be useful, but without ANY WARRANTY; without
#even the implied warranty of merchantability or fitness for a particular purpose.
#Specifically, you may share the software in any medium or format and you may adapt the software.
#Credit must be given when either of these are given to indicate if and what changes were made.
#The software may not be used for noncommerical purposes.
#If you are interested in using the software for commercial purposes, please contact the author above.
###########################################################################################################


#' Gibbs sampler for empirically motivated Bayesian record linkage
#'
#' @param file.num The number of the file
#' @param X.s A vector of string variables
#' @param X.c A vector of categorical variables
#' @param num.gs Total number of gibb iterations
#' @param a Shape parameter of Beta prior
#' @param b Scale parameter of Beta prior
#' @param c Positive constant
#' @param d Any distance metric measuring the latent and observed string
#' @param M The true value of the population size
#' @return Returns the estimated linkage structure via Gibbs sampling
#' @export
rl.gibbs <- function(file.num=file.num,X.s=X.s,X.c=X.c,num.gs=num.gs,a=a,b=b,c=c,d=d,M=M){


	# Get dimensions
	k <- length(unique(file.num))
	N <- length(file.num)
	if(dim(X.s)[1]!=N || dim(X.c)[1]!=N){
		stop("length of file identifier does not match length of record data")
	}
	n <- table(file.num)
	p.s <- dim(X.s)[2]
	p.c <- dim(X.c)[2]
	p <- p.s+p.c

	# Get alpha
	# Note: This is a list of vectors. The lth vector in the list is alpha_l.
	# The w element of alpha_l is alpha_l(w), e.g.,
	# alpha[[2]]["Smith"] is the relative frequency of "Smith" in the 2nd field.

	#print("Creating alpha")
	#print(system.time(
	alpha <- c(lapply(1:p.s, function(i) { table(X.s[,i])/N }),
					lapply(1:p.c, function(i){ table(X.c[,i])/N }))
	#				,gcFirst=FALSE)[3])


	# Get matrix of e^(-c*distance)
	# Note 1: This is a list of matrices, one for each field.
	# Note 2: The idea here is to compute everything ONCE and store it, rather
	# than recomputing over and over at each Gibbs sampling iteration.
	calc_string_distances <- function(l) {
		S <- names(alpha[[l]])
		string_distances <- exp(-c*d(S,S))
		rownames(string_distances) <- S
		colnames(string_distances) <- S
		return(string_distances)
	}
	#print("Calculating ecd")
	#print(system.time(
	ecd <- lapply(1:p.s, calc_string_distances)
	#,gcFirst=FALSE)[3])

	# Get h
	# Note: This is a list of vectors, similar to alpha.
	calc_normalizing_factor <- function(w0, l) {
		return( 1/sum(alpha[[l]]*drop(ecd[[l]][w0,])))
	}
	calc_hl <- function(l) {
		hl <- sapply(1:length(alpha[[l]]), calc_normalizing_factor, l=l)
		names(hl) <- names(alpha[[l]])
		return(hl)
	}
	#print("Getting normalizing factors")
	#print(system.time(
	h <- lapply(1:p.s, calc_hl)
	#,gcFirst=FALSE)[3])

	# Initial values
	beta <- matrix(a/(a+b),nrow=k,ncol=p)
	z <- matrix(0,nrow=N,ncol=p)
	# Here it locks in the latents to the data for varying M, which is how many
	# total latents there could be.
	 Y.s <- matrix(nrow=M, ncol=p.s)
	 Y.c <- matrix(nrow=M, ncol= p.c)
	for(i in 1:M){
		temp <- i %% N
		if (temp==0){
		temp <- N
		}
		Y.s[i,] <- X.s[temp,]
		Y.c[i,] <- X.c[temp,]
	}



	# Use the modulus to take off the remainder if N >= M
	# (That is you have more records than latent entities)
	# If M > N, then we simply just take 1:N
	lambda <- (1:N)%%M
	lambda[lambda==0] <- M

	# Storage for final values (not yet writing to file)
	# beta.out <-
	# z.out <-
	# Y.s.out <-
	# Y.c.out <-
	lambda.out <- matrix(NA,num.gs,N)



	# Function to draw beta
	draw.beta <- function(z){
		output <- matrix(NA,nrow=k,ncol=p)
		draw.beta.i <- function(i) {
			z.sums <- colSums(z[file.num==i,])
			return(rbeta(p,z.sums+a,n[i]-z.sums+b))
		}
		output <- t(sapply(1:k, draw.beta.i))
		return(output)
	}

	# Return a probability proportional to pr.1, unless it's Inf, then return 1
	proportional_or_1 <- function(pr.0,pr.1) {
		ifelse(pr.1==Inf,1,pr.1/(pr.1+pr.0))
	}

	#print("Creating some grids for use with maply")
   #t1 <- system.time(
   ij_by_l_strings <- expand.grid(ij=1:N, l=1:p.s)
   #,gcFirst=FALSE)[3]
   #t2 <- system.time(
   jp_by_l_strings <- expand.grid(jp=1:M, l=1:p.s)
   #,gcFirst=FALSE)[3]
   #t3 <- system.time(
   ij_by_l_cat <- expand.grid(ij=1:N, l=1:p.c)
   #,gcFirst=FALSE)[3]
   #t4 <- system.time(
   jp_by_l_cat <- expand.grid(jp=1:M, l=1:p.c)
   #,gcFirst=FALSE)[3]
   #t5 <- system.time(
   ij_by_l_cat_offset <- expand.grid(ij=1:N, l=p.s+(1:p.c))
   #,gcFirst=FALSE)[3]
   #print(t1+t2+t3+t4+t5)

	calc_pr.1_string <- function(ij, l) {
		X.now <- X.s[ij,l]
		Y.now <- Y.s[lambda[ij],l]
		return(beta[file.num[ij],l]*alpha[[l]][X.now]*h[[l]][Y.now]*ecd[[l]][X.now,Y.now])
	}
	calc_pr.1_cat <- function(ij, l) {
		X.now <- as.character(X.c[ij,l])
		return(beta[file.num[ij],p.s+l]*alpha[[p.s+l]][X.now])
	}
	calc_pr.0 <- function(ij, l) {
		return(1-beta[file.num[ij],l])
	}


	draw.z <- function(Y.s, Y.c, beta, lambda) {
		# Whether string or categorical, z will be a binomial with some probability
		# pr., UNLESS X_{ijl} != Y_{\lambda_{ij}}l}, in which case z_{ijl}=1 automatically
		# Calculate probabilities in pr. vector
		# draw binomials
		# ATTN: This vectorized/plyr'd version is slower than the for-loop-heavy v1
		# below (by about 5 seconds on the test case with num.gs=2).  Why?
		# Some inefficiency in maply(), or are the functions being applied inefficient?

		# Where are there mis-matches between X.s[ij,l] and Y.s[lambda[ij],l]?
		Y.s.now = Y.s[lambda,]
		string_mismatches <- (X.s != Y.s.now)
		Y.c.now = Y.c[lambda,]
		cat_mismatches <- (X.c != Y.c.now)
		# Only need to calculate z probabilities for matches, which we can get
		# by negating



		# Calculate pr.1 for every entry
		  # Different calculations for string fields and categorical fields
		#print("Calculating pr.1 for strings")
		#print(system.time(
		pr.1_string_small <- maply(ij_by_l_strings[!string_mismatches,], calc_pr.1_string, .expand=FALSE)
		# ATTN: it's failing here.

		#, gcFirst=FALSE)[3])
		pr.1_string <- rep(Inf, times=nrow(ij_by_l_strings))
		pr.1_string[!string_mismatches] <- pr.1_string_small
		#print("Calculating pr.1 for categoricals")
		#print(system.time(
		pr.1_cat_small <- maply(ij_by_l_cat[!cat_mismatches,], calc_pr.1_cat, .expand=FALSE)
		#,gcFirst=FALSE)[3])
		pr.1_cat <- rep(Inf, times=nrow(ij_by_l_cat))
		pr.1_cat[!cat_mismatches] <- pr.1_cat_small
		pr.1 <- c(pr.1_string, pr.1_cat)
		# Calculate pr.0 for every entry
		#print("Calculating pr.0 for strings")
		#print(system.time(
		pr.0_string_small <- maply(ij_by_l_strings[!string_mismatches,], calc_pr.0, .expand=FALSE)
		#,gcFirst=FALSE)[3])
		pr.0_string <- rep(0, times=nrow(ij_by_l_strings))
		pr.0_string[!string_mismatches] <- pr.0_string_small
		#print("Calculating pr.0 for categoricals")
		#print(system.time(
		pr.0_cat_small <- maply(ij_by_l_cat_offset[!cat_mismatches,], calc_pr.0, .expand=FALSE)
		#,gcFirst=FALSE)[3])
		pr.0_cat <- rep(0, times=nrow(ij_by_l_cat_offset))
		pr.0_cat[!cat_mismatches] <- pr.0_cat_small
		pr.0 <- c(pr.0_string, pr.0_cat)

		# Combine pr.0 and pr.1 to get pr.
		pr. <- ifelse((pr.1 + pr.0) == 0, 0, proportional_or_1(pr.0,pr.1))

		# assume pr. is at hand
		output <- array(rbinom(N*p,size=1,prob=pr.),dim=c(N,p))
		return(output)
	}

	# Function to draw z: first version based on explicit for loops
	draw.z_v1 <- function(Y.s,Y.c,beta,lambda){
		output <- matrix(NA,nrow=N,ncol=p)
		for(ij in 1:N){
			beta.i <- drop(beta[file.num[ij],])
			for(l in 1:p.s){
				X.now <- as.character(X.s[ij,l])
				Y.now <- as.character(Y.s[lambda[ij],l])
				if(X.now!=Y.now){
					output[ij,l] <- 1
				}else{
					pr.1 <- beta.i[l]*alpha[[l]][X.now]*h[[l]][Y.now]*
							ecd[[l]][X.now,Y.now]
					pr.0 <- 1-beta.i[l]
					if(pr.1+pr.0==0){pr. <- 0}else{pr. <- pr.1/(pr.1+pr.0)}
					output[ij,l] <- rbinom(1,1,pr.)
				}
			}
			for(l in 1:p.c){
				X.now <- as.character(X.c[ij,l])
				Y.now <- as.character(Y.c[lambda[ij],l])
				if(X.now!=Y.now){
					output[ij,p.s+l] <- 1
				}else{
					pr.1 <- beta.i[p.s+l]*alpha[[p.s+l]][X.now]
					pr.0 <- 1-beta.i[p.s+l]
					if(pr.1+pr.0==0){pr. <- 0}else{pr. <- pr.1/(pr.1+pr.0)}
					output[ij,p.s+l] <- rbinom(1,1,pr.)
				}
			}
		}
		return(output)
	}


		draw.Y.s.jpl <- function(jp, l) {
				if(any(lambda==jp & drop(z[,l])==0)){
					# If an undistorted X.ijl is linked to this Y.j'l,
					# then Y.j'l=X.ijl
					return(X.s[which(lambda==jp & z[,l]==0)[1],l])
				}else{
					S <- names(alpha[[l]])
					if(any(lambda==jp)){
						# If all X.ijl linked to this Y.j'l are distorted,
						# then we draw Y.j'l from a distribution
						phi <- h[[l]]*alpha[[l]]
						R.jp <- which(lambda==jp)
						if (length(R.jp)==1) {
							phi <- phi * ecd[[l]][X.s[R.jp,l],]
						} else {
							phi <- phi * apply(ecd[[l]][X.s[R.jp,l],],2,prod)
						}
						#phi <- phi*prod(drop(ecd[[l]][X.s[R.jp,l],]))
						# for(ij in R.jp){
							# phi <- phi*drop(ecd[[l]][X.s[ij,l],])
						# }
						return(sample(S,1,prob=phi))
					}else{
						# If no X.ijl are linked to this Y.j'l, then we draw
						# Y.j'l from the "EB prior"
						return(sample(S,1,prob=alpha[[l]]))
					}
				}
		}


	# Function to draw Y.s
	draw.Y.s <- function(z,lambda){
		output <- maply(jp_by_l_strings, draw.Y.s.jpl, .expand=FALSE)
		output <- matrix(output, nrow=M, ncol=p.s)
		return(output)
	}


	# Function to draw Y.s
	draw.Y.s.v1 <- function(z,lambda){
		output <- matrix(NA,nrow=N,ncol=p.s)
		for(jp in 1:N){
			for(l in 1:p.s){
				if(any(lambda==jp & drop(z[,l])==0)){
					# If an undistorted X.ijl is linked to this Y.j'l,
					# then Y.j'l=X.ijl
					output[jp,l] <- X.s[which(lambda==jp & z[,l]==0)[1],l]
				}else{
					S <- names(alpha[[l]])
					if(any(lambda==jp)){
						# If all X.ijl linked to this Y.j'l are distorted,
						# then we draw Y.j'l from a distribution
						phi <- h[[l]]*alpha[[l]]
						R.jp <- which(lambda==jp)
						for(ij in R.jp){
							phi <- phi*drop(ecd[[l]][X.s[ij,l],])
						}
						output[jp,l] <- sample(S,1,prob=phi)
					}else{
						# If no X.ijl are linked to this Y.j'l, then we draw
						# Y.j'l from the "EB prior"
						output[jp,l] <- sample(S,1,prob=alpha[[l]])
					}
				}
			}
		}
		return(output)
	}


	draw.Y.c.jp.l <- function(jp, l)	 {
		if(any(lambda==jp & drop(z[,p.s+l])==0)){
			# If an undistorted X.ijl is linked to this Y.j'l,
			# then Y.j'l=X.ijl
			return(X.c[which(lambda==jp & z[,p.s+l]==0)[1],l])
		}else{
				# Similar to the draw.Y.s function, except both routes
				# in this part of the code now lead to the same thing
				S <- names(alpha[[p.s+l]])
				return(sample(S,1,prob=alpha[[p.s+l]]))
		}
	}

	# Function to draw Y.c
	draw.Y.c <- function(z,lambda){
		output <- matrix(maply(jp_by_l_cat, draw.Y.c.jp.l, .expand=FALSE),nrow=M, ncol=p.c)
		return(output)
	}

	# Should only be called with a latent (jp) which is eligible for being matched to
	# the observed record ij --- see draw.lambda.ij() below
calc_q <- function(jp, X.c.ij, X.s.ij, z.s.ij, z.c.ij) {
		Y.s.jp <- drop(Y.s[jp,])
		Y.c.jp <- drop(Y.c[jp,])
		# Probability factor for the distorted strings
		hYecd <- 1
		distorted_strings <- which(z.s.ij==1)
		if (length(distorted_strings) > 0) {
			hYecd <- sapply(distorted_strings, function(l) { h[[l]][Y.s.jp[l]]*ecd[[l]][X.s.ij[l],Y.s.jp[l]] } )
		}
		# # Probability factor for the distorted categories
		# alphas <- 1
		# distorted_cats <- which(z.c.ij==1)
		# if (length(distorted_cats) > 0) {
			# alphas <- sapply(distorted_cats, function(l) {
				# # Obscurely, using single braces here gives us a list, and crashes
				# X.now <- X.c.ij[[l]]
				# alpha.now <- alpha[[l+p.s]]
				# alpha.now[as.character(X.now)] })
		# }
		q.jp <- prod(hYecd)  # *prod(alphas)
		return(q.jp)
	}


	latent_string_nonmatch <- function(l, X.s.ij) { which(X.s.ij[l] != Y.s[,l]) }
	latent_cat_nonmatch <- function(l, X.c.ij) { which(X.c.ij[l] != Y.c[,l]) }


	draw.lambda.ij <- function(ij) {
		# ATTN: This takes much too long! (13 seconds per Gibbs iteration), key bottleneck
		X.s.ij <- drop(X.s[ij,])
		X.c.ij <- drop(X.c[ij,])
		z.s.ij <- drop(z[ij,1:p.s])
		z.c.ij <- drop(z[ij,(p.s+1):p])



		# v is not a possible latent for ij if z[ij,l] = 0 but X[ij,l] != Y[v,l]
		# Otherwise, v is a possible latent
		# build set of impossible latents
		   # only need to consider fields where z[ij,l] ==0
		undistorted_string_fields <- which(z.s.ij == 0)
		undistorted_cat_fields <- which(z.c.ij == 0)
		impossible_string_latents <- lapply(undistorted_string_fields, latent_string_nonmatch, X.s.ij=X.s.ij)
		impossible_string_latents <- unique(do.call("c",impossible_string_latents))
		impossible_cat_latents <- lapply(undistorted_cat_fields, latent_cat_nonmatch, X.c.ij = X.c.ij)
		impossible_cat_latents <- unique(do.call("c",impossible_cat_latents))
		impossible_latents <- union(impossible_string_latents, impossible_cat_latents)
		possible_latents <- setdiff(1:M, impossible_latents)


		if(length(possible_latents)==1) {
			return(possible_latents)
		} else {
			q <- sapply(possible_latents, calc_q, X.s.ij=X.s.ij, X.c.ij=X.c.ij, z.s.ij=z.s.ij, z.c.ij=z.c.ij)

			return(sample(possible_latents,size=1,prob=q))
		}
	}



	# Function to draw lambda
	draw.lambda <- function(Y.s,Y.c,z){
		output <- sapply(1:N, draw.lambda.ij)
		return(output)
	}




	timestamp <- format(Sys.time(), "%Y%m%d-%H%M%S")
	outputfilename <- paste("lambda-",timestamp,".txt",sep="")

	for(gs.iter in 1:num.gs){
	  print(sprintf("Gibbs sampler iteration %i", gs.iter))
		print("     Drawing beta")
		beta <- draw.beta(z)
		print("     Drawing z")
		z <- draw.z(Y.s,Y.c,beta,lambda)
		print("     Drawing Y.s")
		Y.s <- draw.Y.s(z,lambda)
		print("     Drawing Y.c")
		Y.c <- draw.Y.c(z,lambda)
		print("     Drawing lambda")
		lambda <- draw.lambda(Y.s,Y.c,z)
		print("     Updating lambda history")
		lambda.out[gs.iter,] <- lambda
		write.table(matrix(lambda,nrow=1),outputfilename,append=TRUE,
			row.names=FALSE,col.names=FALSE)
		flush.console()
	}

	return(lambda.out)
}



