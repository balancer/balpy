import balpy


def main():
    network = "mainnet"
    bal = balpy.balpy.balpy(network)

    # NOTE: Using these time-based gas strategies requires caching gas prices over
    # extended time periods. In testing, this script made 140-150 calls to the RPC
    # and took ~1 minute to initialize the cache.

    speeds = ["slow", "average", "fast"]
    print("\n\tSpeed\tPrice(gwei)")
    print("\t-----\t-----------")
    for speed in speeds:
        price = bal.getGasPrice(speed)
        print("\t" + speed + "\t" + str(price))


if __name__ == "__main__":
    main()
