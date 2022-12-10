import balpy


def main():
    network = "mainnet"

    bal = balpy.balpy.balpy(network)

    print("Successful Case:")
    poolId = "0x5c6ee304399dbdb9c8ef030ab642b10820db8f56000200000000000000000014"
    factoryName = bal.balFindPoolFactory(poolId)
    print(poolId, "is from", factoryName)

    print("-----------------------------------")

    print("Failure Case:")
    poolId = "0x01234567899dbdb9c8ef030ab642b10820db8f56000200000000000000000014"
    factoryName = bal.balFindPoolFactory(poolId)
    print(poolId, "is from", factoryName)


if __name__ == "__main__":
    main()
