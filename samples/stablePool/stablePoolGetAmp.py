import balpy


def main():
    network = "kovan"

    bal = balpy.balpy.balpy(network)
    poolId = "0x6b15a01b5d46a5321b627bd7deef1af57bc629070000000000000000000000d4"
    (value, isUpdating, precision) = bal.balStablePoolGetAmplificationParameter(poolId)
    print("value:", value)
    print("isUpdating:", isUpdating)
    print("precision:", precision)


if __name__ == "__main__":
    main()
