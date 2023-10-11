import balpy


def main():
    print("In this test we'll set the user address as the relayer and then remove it.")
    print(
        "It doesn't make sense to set the user as the relayer, but this is just a test."
    )
    print("==============================================")

    bal = balpy.balpy.balpy("goerli")
    userAddress = bal.web3.eth.default_account
    print(
        "Before set approved relayer:",
        bal.balVaultHasApprovedRelayer(userAddress, userAddress),
    )
    print()

    bal.balVaultSetRelayerApproval(userAddress, userAddress, True)
    print(
        "After set approved relayer:",
        bal.balVaultHasApprovedRelayer(userAddress, userAddress),
    )

    bal.balVaultSetRelayerApproval(userAddress, userAddress, False)
    print(
        "After unset approved relayer:",
        bal.balVaultHasApprovedRelayer(userAddress, userAddress),
    )
    print()


if __name__ == "__main__":
    main()
