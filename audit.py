import argparse
import os

# Importing code from Philip's SHANGRLA repository
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Input: data file
    parser.add_argument('-d', action='store', dest='data')

    # Input: anticipated error rate (default value maps to 2 1 vote
    # overstatements per 1000 ballots)
    parser.add_argument('-e', action='store', dest='erate', default=0.002)

    # Input: risk limit (default is 5%)
    parser.add_argument('-r', action='store', dest='rlimit', default=0.05)

    # Input: number of repetitions to perform in simulation to determine
    # an initial sample size estimation -- the quantile of the sample
    # size is computed (default is 20 repetitions)
    parser.add_argument('-reps', action='store', dest='reps', default=20)

    # Input: seed (default is 93686630803205229070)
    parser.add_argument('-s', action='store', dest='seed', \
        default=93686630803205229070)

    args = parser.parse_args()

    # data is a mapping between party name and a (votes, seats) tuple
    data, tot_ballots = read_data(args.data)

    # compute total number of votes and seats
    tot_votes = 0
    tot_seats = 0

    for p,(v,s) in data.items():
        tot_votes += v
        tot_seats += s

    TBTS = tot_ballots*tot_seats

    # Kaplan Martingale risk function is used
    risk_function = "kaplan_martingale"
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
            sample_size =  TestNonnegMean.initial_sample_size(risk_fn, \
                tot_ballots, m, args.erate, alpha=0.05, t=1/2, reps=args.reps,\
                bias_up=True, quantile=0.5, seed=args.seed)
            
            max_sample = max(sample_size, max_sample)

            # Print out: Party name 1, Party name 2, proportion of votes
            # in Party 1's tally, proportion of votes in Party 2's tally,
            # value of 'd', margin, and estimate of initial sample required
            # to audit the assertion.
            print("{},{},{},{},{},{},{}".format(p1, p2, v1/tot_votes,\
                v2/tot_votes, d, m, sample_size))

    print("Overal ASN: {} ballots".format(max_sample))
