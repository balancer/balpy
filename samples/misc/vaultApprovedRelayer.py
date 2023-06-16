import balpy

def main():
    print("This test we'll set the user address as relayer and then remove it.")
    print("Don't make sense setting the user as relayer, but it's just a test.")
    print("==============================================")

    bal = balpy.balpy.balpy("goerli")
    userAddress = bal.web3.eth.default_account
    print("Before ser approved relayer:", bal.balVaultHasApprovedRelayer(userAddress, userAddress))
    print()

    bal.balVaultSetRelayerApproval(userAddress, userAddress, True)
    print("After set approved relayer:", bal.balVaultHasApprovedRelayer(userAddress, userAddress))

    bal.balVaultSetRelayerApproval(userAddress, userAddress, False)
    print("After reversed operation:", bal.balVaultHasApprovedRelayer(userAddress, userAddress))
    print()

if __name__ == '__main__':
    main()
