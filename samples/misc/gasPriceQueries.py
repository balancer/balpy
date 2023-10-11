import time

import balpy


def main():
    network = "mainnet"
    bal = balpy.balpy.balpy(network)

    speeds = ["slow", "average", "fast"]

    # NOTE: Using these time-based gas strategies requires caching gas prices over
    # extended time periods. In testing, this script made 140-150 calls to the RPC
    # and took ~1 minute to initialize the cache.
    start = time.time()
    print("\n--- RPC Method -----------------------------")
    print("\tSpeed\tPrice(gwei)")
    print("\t-----\t-----------")
    for speed in speeds:
        price = bal.getGasPrice(speed)
        print("\t" + speed + "\t" + str(price))
    print("\nRPC gas queries took", time.time() - start, "seconds\n")

    # Etherscan gas prices
    start = time.time()
    print("\n--- Etherscan Method -----------------------")
    print("\tSpeed\tPrice(gwei)")
    print("\t-----\t-----------")
    for speed in speeds:
        price = bal.getGasPriceEtherscanGwei(speed)
        print("\t" + speed + "\t" + str(price))
    print("\nEtherscan gas queries took", time.time() - start, "seconds\n")


if __name__ == "__main__":
    main()
