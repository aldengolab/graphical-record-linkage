"
Emperical Validation of Theoretical Lower Bounds
Author: mbarnes1@cs.cmu.edu
"
rm(list=ls())
source('model.R')
source('conditionals.R')

# Experiment parameters
n = 500
betas <- seq(from = 0.1, to = 0.9, by = 0.1)
thetas <- list(rep(0.1, 10), rep(0.1, 10), rep(0.1, 10))

L <- length(thetas)  # number of fields
# Sweep through experiment parameters
accuracy_predicted <- rep(NA, length(betas))
bound_expected_accuracy <- rep(NA, length(betas))

for (ibeta in 1:length(betas)) {
  # Draw synthetic data
  beta <- rep(betas[ibeta], L)
  Lambda <- model.draw.Lambda(n)
  Y.c <- model.draw.Y.c(thetas, n)
  z <- model.draw.z(beta, n)
  X.c <- model.draw.X.c(Lambda, Y.c, z, thetas)
  Y.s <- array(rep('x',n), dim=c(n,1))  # dummy strings, sampler will not run without this
  X.s <- array(Y.s[Lambda,], dim=c(n,1))
  z <- cbind(rep(0,n), z)  # zero distortion on dummy string
  
  # Compute theoretical lower bound
  gamma <- 0
  minthetas <- sapply(thetas,min)
  for (i in 1:n) {  # gamma is upper bound on largest KL divergence between any two linkages
    for (prime in 1:n)  {
      ind <- Y.c[i,] != Y.c[prime,]
      gamma_ip <- sum(ind*(1-beta)*log(1/(beta*minthetas)))
      gamma <- max(gamma, gamma_ip)
    }
  }
  pr_error <- 1-(gamma + log(2))/log(n+1)
  bound_expected_accuracy[ibeta] <- pr_error
  
  # Run experiment
  Lambda.predicted <- conditionals.draw.lambda(Y.s,Y.c,z)
  accuracy_predicted[ibeta] <- sum(Lambda != Lambda.predicted)/n
}
# Plot the results
plot(betas, accuracy_predicted, type="b", col="red", ylim=c(0, max(accuracy_predicted)), ann=FALSE)
lines(betas, bound_expected_accuracy, type='b', col="blue")
title(main='Experimental Bound Validation', xlab='beta', ylab='Accuracy')

legend('topleft', c("Exact Sampling","Bound"), cex=1, 
       col=c("red","blue"), lty=1:3, lwd=2, bty="n")
