Auditing Free List Hamiltonian elections.
-----------------------------------------

This repository contains code for determining the set of assertions required to audit the distribution of seats in a Free List Hamiltonian election. This code requires the file assertion_audit_utils.py from https://github.com/pbstark/SHANGRLA/tree/main/Code.


Data has been provided for a local election in Hesse in 2016, summarised from online sources (https://www.statistik-hessen.de/k2016/html/index.htm).

A script has been provided for running the experiments in the paper: "Assertion-based approaches to auditing complex elections".

Usage (example with 0 error rate and 5% risk limit): 

python3 audit.py -d data/Local_Hesse_2016/Bergstrasse.csv -r 0.05 -g 0.1 -e 0 -reps 1 
