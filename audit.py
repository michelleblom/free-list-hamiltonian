import argparse
import os
import statistics

import numpy as np

# Importing code from Philip's SHANGRLA repository:
# https://github.com/pbstark/SHANGRLA/tree/main/Code
from assertion_audit_utils import TestNonnegMean

# Read summarised election data from file.
# File has the following format:
# VOTERS,Number of voters
# INVALID,Number of invalidly cast ballots
# PARTY,VOTES,SEATS
# Party name,Votes in party's tally,Seats awarded
# Party name,Votes in party's tally,Seats awarded
# ...
# Party name,Votes in party's tally,Seats awarded
#
# The total number of valid ballots cast in the election
# is computed as Number of voters - Number of invalidly
# cast ballots.
def read_data(dfile):
    data = {}
    tot_ballots = 0
    with open(dfile, 'r') as f:
        lines = f.readlines()

        toks1 = lines[0].split(',')
        toks2 = lines[1].split(',')
        
        tot_ballots = int(toks1[1]) - int(toks2[1])

        # Skip first three lines: party votes & seats 
        # attributions start on the 4th line.
        for i in range(3, len(lines)):
            # line = Party,Votes,Seats
            toks = lines[i].split(',')

            data[toks[0]] = (int(toks[1]), int(toks[2]))

    return data, tot_ballots

# This function extracts code from audit_assertion_utils.py in the 
# SHANGRLA repository.
def sample_size_kaplan_kolgoromov(margin, prng, N, error_rate, rlimit, t=1/2, \
    g=0.1, quantile=0.5, reps=20):

    clean = 1.0/(2 - margin)
    one_vote_over = 0.5/(2-margin)

    samples = [0]*reps

    for i in range(reps):
        pop = clean*np.ones(N)
        inx = (prng.random(size=N) <= error_rate)  # randomly allocate errors
        pop[inx] = one_vote_over

        sample_total = 0
        mart = (pop[0]+g)/(t+g) if t > 0 else  1
        p = min(1.0/mart,1.0)
        j = 1

        while p > rlimit and j < N:
            mart *= (pop[j]+g)*(1-j/N)/(t+g - (1/N)*sample_total)
    
            if mart < 0:
                break
            else:
                sample_total += pop[j] + g

            p = min(1.0/mart,1.0)
            j += 1;

        if p <= rlimit:
            samples[i] = j
        else:
            return np.inf 

    return np.quantile(samples, quantile)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Input: data file
    parser.add_argument('-d', action='store', dest='data')

    # Input: anticipated error rate (default value maps to 2 1 vote
    # overstatements per 1000 ballots)
    parser.add_argument('-e', action='store', dest='erate', default=0.002)

    # Input: risk limit (default is 5%)
    parser.add_argument('-r', action='store', dest='rlimit', default=0.05)
    
    # Input: parameter for some risk functions
    parser.add_argument('-g', action='store', dest='g', default=0.1)

    # Input: parameter for some risk functions
    parser.add_argument('-t', action='store', dest='t', default=1/2)
    
    # Risk function to use for estimating sample size
    parser.add_argument('-rf', action='store', dest='rfunc', \
        default="kaplan_kolmogorov")

    # Input: number of repetitions to perform in simulation to determine
    # an initial sample size estimation -- the quantile of the sample
    # size is computed (default is 20 repetitions)
    parser.add_argument('-reps', action='store', dest='reps', default=20)

    # Input: seed (default is 93686630803205229070)
    parser.add_argument('-s', action='store', dest='seed', \
        default=9368663)

    args = parser.parse_args()

    # data is a mapping between party name and a (votes, seats) tuple
    data, tot_ballots = read_data(args.data)

    # compute total number of votes and seats
    tot_votes = 0
    tot_seats = 0

    seed = int(args.seed)
    erate = float(args.erate)
    rlimit = float(args.rlimit)

    REPS = int(args.reps)
    t = float(args.t)
    g = float(args.g)
    
    for p,(v,s) in data.items():
        tot_votes += v
        tot_seats += s

    TBTS = tot_ballots*tot_seats

    risk_fn = lambda x: TestNonnegMean.kaplan_martingale(x, N=tot_ballots)[0]

    # for each pair of parties, in both directions, compute
    # margin for pairwise c-diff assertion
    max_sample = 0
    for p1 in data:
        for p2 in data:
            if p1 == p2:
                continue

            v1,a1 = data[p1]
            v2,a2 = data[p2]

            # compute 'd'
            d = (a1 - a2 - 1)/tot_seats

            # Compute mean of assorter for assertion and margin 'm'
            amean = ((v1 - v2) - tot_votes*d + TBTS*(1+d))/(2*TBTS*(1+d))

            m = 2*(amean) - 1
       
            # Estimate sample size via simulation
            sample_size = np.inf
            if args.rfunc == "kaplan_kolmogorov":
                prng = np.random.RandomState(seed) 
                sample_size =  sample_size_kaplan_kolgoromov(m, prng, \
                    tot_ballots, erate, rlimit, t=t, g=g, quantile=0.5,\
                    reps=REPS)
            else:
                # Use kaplan martingale
                risk_fn = lambda x: TestNonnegMean.kaplan_martingale(x, \
                    N=tot_ballots)[0]
                
                sample_size =  TestNonnegMean.initial_sample_size(risk_fn, \
                    tot_ballots, m, erate, alpha=rlimit, t=t, reps=REPS,\
                    bias_up=True, quantile=0.5, seed=seed)
            
            max_sample = max(sample_size, max_sample)

            # Print out: Party name 1, Party name 2, proportion of votes
            # in Party 1's tally, proportion of votes in Party 2's tally,
            # value of 'd', margin, and estimate of initial sample required
            # to audit the assertion.
            print("{},{},{},{},{},{},{}".format(p1, p2, v1/tot_votes,\
                v2/tot_votes, d, m, sample_size))

    print("Overal ASN: {} ballots".format(max_sample))
