import json
import time

import requests

import balpy


def main():
    network = "mainnet"
    bal = balpy.balpy.balpy(network)

    poolIdsUrl = (
        "https://raw.githubusercontent.com/gerrrg/balancer-pool-ids/master/pools/"
        + network
        + ".json"
    )
    r = requests.get(poolIdsUrl)
    poolIds = r.json()["pools"]

    if "Element" in poolIds.keys():
        del poolIds["Element"]

    tStart = time.time()
    results = bal.getOnchainData(poolIds)
    tEnd = time.time()
    print("Query took", tEnd - tStart, "seconds")

    print(json.dumps(results, indent=4))


if __name__ == "__main__":
    main()
