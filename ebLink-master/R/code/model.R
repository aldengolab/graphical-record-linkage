model.draw.z <- function(beta, n) {
  "
  Inputs:
    beta - vector corruption probabilities
    n - number of records
  Outputs:
    z - array of size n x length(beta)
  "
  L <- length(beta)  # number of fields 
  z <- array(NA, dim=c(n, L))
  for (i in 1:L) {
    z[,i] <- rbinom(n, size=1, prob=beta[i])
  }
  return(z)
}

model.draw.Y.c <- function(thetas, n) {
  "
  Inputs:
    thetas - List of categorical probability vector (not necessarily all the same length)
  Outputs:
    Y - n x length(theta) array. (b/c number of latent individuals can be at most n)
  "
  L <- length(thetas)
  Y.c <- array(NA, dim=c(n,L))
  for (i in 1:L) {
    theta <- thetas[[i]]
    Y.c[,i] <- which(rmultinom(n, size=1, prob=theta)!=0, arr.ind=T)[,1]
  }
  return(Y.c)
}

model.draw.Lambda <- function(n) {
  "
  Inputs:
    n - number of records (and potential latent individuals)
  Outputs:
    Lambda - vector of length n, which latent individual each record belongs to
  "
  Lambda <- sample(1:n, n)
  return(Lambda)
}

model.draw.X.c <- function(Lambda, Y.c, z, thetas) {
  "
  Inputs:
    Lambda - Linkage structure (vector of length n)
    Y.c - Latent entities (n x numberfields array)
    z - Binary corruption array (n x numberfields array)
    thetas - Field probabilities (numberfields length list of probability vectors)
  Outputs:
    X.c - Observed records (n x numberfields array)
  "
  n <- length(Lambda)
  Y.c.corruption <- model.draw.Y.c(thetas, n)
  X.c.uncorrupted <- Y.c[Lambda,]
  X.c <- X.c.uncorrupted*(1-z) + Y.c.corruption*z
  return(X.c)
}

"
# Example
n = 10  # number of records
m = 3  # number of fields
beta = runif(m)
print(beta)
z <- model.draw.z(beta, n)
print(z)
theta1 = c(0.5, 0.4, 0.1)
theta2 = c(1)
theta3 = rep(0.1, 10)
thetas = list(theta1, theta2, theta3)
Y.c <- model.draw.Y.c(thetas, n)
print(Y.c)
Lambda <- model.draw.Lambda(n)
print(Lambda)
X.c <- model.draw.X.c(Lambda, Y.c, z, thetas)
print(X.c)
"


