import balpy


def main():
    network = "mainnet"

    bal = balpy.balpy.balpy(network)
    poolId = "0x96646936b91d6b9d7d0c47c496afbf3d6ec7b6f8000200000000000000000019"

    # enum Variable { PAIR_PRICE, BPT_PRICE, INVARIANT }
    # struct OracleAverageQuery {
    #     Variable variable;
    #     uint256 secs;
    #     uint256 ago;
    # }
    variable = 0
    # pair price
    secs = 60 * 60 * 24
    # one day
    ago = 0
    # most recent

    queries = []
    queries.append((variable, secs, ago))
    results = bal.balOraclePoolGetTimeWeightedAverage(poolId, queries)

    print(results[0])


if __name__ == "__main__":
    main()
