import balpy


def main():
    network = "kovan"

    bal = balpy.balpy.balpy(network)
    output = bal.generateDeploymentsDocsTable()
    print(output)


if __name__ == "__main__":
    main()
