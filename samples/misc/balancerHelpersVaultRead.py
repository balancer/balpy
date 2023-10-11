import balpy


def main():
    network = "polygon"

    bal = balpy.balpy.balpy(network)
    vaultAddress = bal.balBalancerHelpersGetVault()
    print("Vault address:", vaultAddress)


if __name__ == "__main__":
    main()
