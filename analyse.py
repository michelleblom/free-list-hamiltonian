import os
import sys

if __name__ == "__main__":

    for filename in os.listdir(sys.argv[1]):
        path = sys.argv[1] + "/" + filename
        with open(path, 'r') as f:
            lines = f.readlines()

            # last three lines have summaries
            l = len(lines)
            toks1 = lines[l-3].split()
            toks2 = lines[l-2].split()
            toks3 = lines[l-1].split()

            print("Level 0: {},{}".format(filename, toks1[4]))
            print("Level 1: {},{}".format(filename, toks2[4]))
            print("Level 2: {},{}".format(filename, toks3[4]))
