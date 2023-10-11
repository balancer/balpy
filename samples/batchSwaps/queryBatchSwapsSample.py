import json
import os
import sys

import balpy


def main():

    if len(sys.argv) < 2:
        print("Usage: python3", sys.argv[0], "/path/to/swap.json")
        quit()

    pathToSwap = sys.argv[1]
    if not os.path.isfile(pathToSwap):
        print("Path", pathToSwap, "does not exist. Please enter a valid path.")
        quit()

    with open(pathToSwap) as f:
        data = json.load(f)

    bal = balpy.balpy.balpy(data["network"])

    swap = data["batchSwap"]
    (data, successes) = bal.balQueryBatchSwaps([swap] * 3)
    print(successes)
    print(json.dumps(data, indent=4))


if __name__ == "__main__":
    main()
