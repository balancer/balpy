import balpy


def main():
    network = "sepolia"

    linear_pool_address = "0x27b26a3d2080b30036faa0a980a76d4770cddaff"

    bal = balpy.balpy.balpy(network)
    bal.balDoRebalanceLinearPool(linear_pool_address)


if __name__ == "__main__":
    main()
