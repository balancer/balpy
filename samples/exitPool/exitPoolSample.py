import balpy
import sys
import os
import jstyleson
import json


def main():
    if len(sys.argv) < 2:
        print("Usage: python3", sys.argv[0], "/path/to/exitData.json")
        quit()

    pathToExit = sys.argv[1]
    if not os.path.isfile(pathToExit):
        print("Path", pathToExit, "does not exist. Please enter a valid path.")
        quit()

    with open(pathToExit) as f:
        exitData = jstyleson.load(f)

    bal = balpy.balpy.balpy(exitData["network"])

    print()
    print("==============================================================")
    print("================ Step 1: Check Bpt Balance ===================")
    print("==============================================================")
    print()

    poolAddress = bal.balPooldIdToAddress(exitData["poolId"])
    if not bal.erc20HasSufficientBalances([poolAddress], [exitData["bptAmount"]]):
        print("Please fix your insufficient BPT balance before proceeding.")
        print("Quitting...")
        quit()

    print()
    print("==============================================================")
    print("================== Step 2: Send Bpt to Pool ==================")
    print("==============================================================")
    print()

    query = False
    output = bal.balExitPool(exitData, query=query)

    if query:
        print("queryExit results:")
        print(json.dumps(output, indent=4))


if __name__ == '__main__':
    main()
