import os
import sys

if __name__ == "__main__":

    for filename in os.listdir(sys.argv[1]):
        path = sys.argv[1] + "/" + filename
        with open(path, 'r') as f:
            lines = f.readlines()

            # last line has summary
            toks = lines[-1].split()

            print("{},{}".format(filename, toks[2]))
