# import graph
import sys

import balpy.graph.graph as balGraph


def main(network="mainnet"):

    batch_size = 100
    networks = ["mainnet", "kovan", "polygon", "gnosis-chain"]

    if network not in networks:
        print("Network", network, "is not supported!")
        print("Supported networks are:")
        for n in networks:
            print("\t" + n)
        print("Quitting")
        quit()

    verbose = False
    bg = balGraph.TheGraph(network)
    pools = bg.getV2PoolIDs(batch_size, verbose=verbose)
    bg.printJson(pools)


if __name__ == "__main__":
    print()

    if len(sys.argv) < 2:
        print("Usage: python", sys.argv[0], "<network>")
        print("No network given; defaulting to mainnet Ethereum")
        network = "mainnet"
    else:
        network = sys.argv[1]

    main(network)
