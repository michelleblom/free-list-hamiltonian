import argparse
import os
import statistics
import math

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
    tot_voters = 0
    with open(dfile, 'r') as f:
        lines = f.readlines()

        toks1 = lines[0].split(',')
        toks2 = lines[1].split(',')
        
        tot_ballots = int(toks1[1]) - int(toks2[1])
        tot_voters = int(toks1[1])

        # Skip first three lines: party votes & seats 
        # attributions start on the 4th line.
        for i in range(3, len(lines)):
            # line = Party,Votes,Seats
            toks = lines[i].split(',')

            data[toks[0]] = (int(toks[1]), int(toks[2]))

    return data, tot_ballots, tot_voters

# This function extracts code from audit_assertion_utils.py in the 
# SHANGRLA repository.
def sample_size_kaplan_kolgoromov(margin, prng, N, error_rate, rlimit, t=1/2, \
    g=0.1, upper_bound=1, quantile=0.5, reps=20):

    clean = 1.0/(2 - margin/upper_bound)
    one_vote_over = (1-0.5)/(2-margin/upper_bound) 

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

            
            p = min(1.0/mart,1.0) if mart > 1.0 else 1.0

            j += 1;

        if p <= rlimit:
            samples[i] = j
        else:
            return np.inf 

    return np.quantile(samples, quantile)


def supermajority_sample_size(hquota, seats, tot_votes, tot_ballots, \
    tot_voters, erate, rlimit, t, g, REPS, seed, rfunc):

    threshold = (hquota*seats)/tot_votes

    # supermajority assertion: party p1 achieved 
    # more than 'threshold' of the vote.
    share = 1.0/(2*threshold)
    
    amean = (1.0/tot_voters)*(v1*share) - \
        tot_votes/(2*tot_voters) + 0.5

    m = 2*amean - 1

    # Estimate sample size via simulation
    sample_size = np.inf
    if rfunc == "kaplan_kolmogorov":
        prng = np.random.RandomState(seed) 
        sample_size =  sample_size_kaplan_kolgoromov(m, prng, tot_ballots, \
            erate, rlimit, t=t, g=g, upper_bound=share,quantile=0.5, reps=REPS)
    else:
        # Use kaplan martingale
        risk_fn=lambda x: TestNonnegMean.kaplan_martingale(x,N=tot_ballots)[0]
                
        sample_size =  TestNonnegMean.initial_sample_size(risk_fn, \
            tot_ballots, m, erate, alpha=rlimit, t=t, upper_bound=share,\
            reps=REPS, bias_up=True, quantile=0.5, seed=seed)

    return sample_size, m, threshold, amean

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
    data, tot_ballots, tot_voters = read_data(args.data)

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

    print("{} seats, {} voters, {} parties, {} valid ballots, "\
        "{} total votes".format(tot_seats, tot_voters, len(data), \
        tot_ballots, tot_votes)) 

    TBTS = tot_ballots*tot_seats
    iballots = tot_voters - tot_ballots

    level0_max_sample = 0
    level1_max_sample = 0

    # Check that party deserved all but their last seat
    hquota = tot_votes/tot_seats
    for p1 in data:
        v1,a1 = data[p1]

        if a1 > 1:
            sample_size,m, th, am = supermajority_sample_size(hquota, a1-1, \
                tot_votes, tot_ballots, tot_voters, erate, rlimit, t, g, \
                REPS, seed, args.rfunc)
            
            level0_max_sample = max(sample_size, level0_max_sample)
            
            print("Level 0,{},{},{},{},{}".format(p1, a1-1, th, m, sample_size))

        if a1 > 0:
            v_div_q = math.floor(tot_seats*(v1 / tot_votes)) 
            
            if v_div_q > 0:
                sample_size,m, th, am = supermajority_sample_size(hquota, \
                    v_div_q, tot_votes, tot_ballots, tot_voters, erate, \
                    rlimit, t, g, REPS, seed, args.rfunc)
            
                print("Level 1,{},{},{},{},{}".format(p1, v_div_q, th, \
                    m, sample_size))

                level1_max_sample = max(sample_size, level1_max_sample)


    # for each pair of parties, in both directions, compute
    # margin for pairwise c-diff assertion
    level2_max_sample = 0
    num_level2 = 0
    for p1 in data:
        for p2 in data:
            if p1 == p2:
                continue

            v1,a1 = data[p1]
            v2,a2 = data[p2]

            # compute 'd'
            d = (a1 - a2 - 1)/tot_seats

            # Compute mean of assorter for assertion and margin 'm'
            # formerly before change to include invalid ballots
            amean = (1.0/tot_voters) * (((v1 - v2) - tot_votes*d + \
                TBTS*(1+d))/(2*tot_seats*(1+d)) + iballots/2.0)

            m = 2*(amean) - 1
       
            upper = 1/(1+d)

            # Estimate sample size via simulation
            sample_size = np.inf
            if args.rfunc == "kaplan_kolmogorov":
                prng = np.random.RandomState(seed) 
                sample_size =  sample_size_kaplan_kolgoromov(m, prng, \
                    tot_ballots, erate, rlimit, t=t, g=g, upper_bound=upper,\
                    quantile=0.5,reps=REPS)
            else:
                # Use kaplan martingale
                risk_fn = lambda x: TestNonnegMean.kaplan_martingale(x, \
                    N=tot_ballots)[0]
                
                sample_size =  TestNonnegMean.initial_sample_size(risk_fn, \
                    tot_ballots, m, erate, alpha=rlimit, t=t, reps=None,\
                    bias_up=True, quantile=0.5, seed=seed)
            
            level2_max_sample = max(sample_size, level2_max_sample)

            # Print out: Party name 1, Party name 2, proportion of votes
            # in Party 1's tally, proportion of votes in Party 2's tally,
            # value of 'd', margin, and estimate of initial sample required
            # to audit the assertion.
            print("Level 2,{},{},{},{},{},{},{}".format(p1, p2, v1/tot_votes,\
                v2/tot_votes, d, m, sample_size))

            num_level2 += 1

    print("Level 0, Overal ASN: {} ballots".format(level0_max_sample))
    print("Level 1, Overal ASN: {} ballots".format(level1_max_sample))
    print("Level 2, Overal ASN: {} ballots, {} assertions".format(\
        level2_max_sample, num_level2))
