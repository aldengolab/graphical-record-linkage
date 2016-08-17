source('~/work_on/Rpackage/ebLink/R/code/ebGibbsSampler.R', chdir = TRUE)
source('~/work_on/Rpackage/ebLink/R/examples/setParamsGermanData.R', chdir = TRUE)
# varying a with a+b = 100

# This run is for 0.0001
system.time(lam.gs <- rl.gibbs(file.num,X.s,X.c,num.gs=2,a=.01,b=100,c=1,d, M=500))
# This run is for 0.1
#system.time(lam.gs <- rl.gibbs(file.num,X.s,X.c,num.gs=10,a=10,b=99,c=1,d, M=500))
# This is for 1
#system.time(lam.gs <- rl.gibbs(file.num,X.s,X.c,num.gs=10,a=99,b=100,c=1,d, M=500))
# This is for 2.5
#system.time(lam.gs <- rl.gibbs(file.num,X.s,X.c,num.gs=10,a=250,b=100,c=1,d,M=500))
# This is for 5
#system.time(lam.gs <- rl.gibbs(file.num,X.s,X.c,num.gs=10,a=500,b=100,c=1,d, M=500))

outer_jarowinkler <- function(string1,string2) { outer(string1, string2, jarowinkler) }
# Comment out next line to use edit distance rather than JW
d <- outer_jarowinkler

# This run is for 0.0001
system.time(lam.gs <- rl.gibbs(file.num,X.s,X.c,num.gs=2,a=.01,b=100,c=1,d,M=500))
# This run is for 0.1
#system.time(lam.gs <- rl.gibbs(file.num,X.s,X.c,num.gs=10,a=10,b=99,c=1,d))
# This is for 1
#system.time(lam.gs <- rl.gibbs(file.num,X.s,X.c,num.gs=10,a=99,b=100,c=1,d))
# This is for 2.5
#system.time(lam.gs <- rl.gibbs(file.num,X.s,X.c,num.gs=10,a=250,b=100,c=1,d))
# This is for 5
#system.time(lam.gs <- rl.gibbs(file.num,X.s,X.c,num.gs=10,a=500,b=100,c=1,d))



