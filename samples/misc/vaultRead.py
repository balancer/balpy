import balpy

NETWORK = "mainnet"
POOLID = "0x32296969ef14eb0c6d29669c550d4a0449130230000200000000000000000080"
TOKENADDRESS = "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0"
USER = "0x0000000000000000000000000000000000000000"
BAL = balpy.balpy.balpy(NETWORK)


def WETH():
    wethAddress = BAL.balVaultWeth()
    print("Weth address:", wethAddress)


def getAuthorizer():
    authorizer = BAL.balVaultGetAuthorizer()
    print("Authorizer address:", authorizer)


def getPool():
    poolAddress, specialization = BAL.balVaultGetPool(POOLID)
    print("Pool:", poolAddress)
    print("Specialization:", specialization)

    
def getPoolTokenInfo():
    cash, managed, lastChangeBlock, assetManager = BAL.balVaultGetPoolTokenInfo(POOLID, TOKENADDRESS)
    print("Cash:", cash)
    print("Managed:", managed)
    print("Last Changed Block:", lastChangeBlock)
    print("Asset Manager:", assetManager)


def getPoolTokens():
	(tokens, balances, lastChangeBlock) = BAL.balVaultGetPoolTokens(POOLID);
	print("Token\t\t\t\t\t\tBalance (wei)")
	print("-----\t\t\t\t\t\t-------------")
	for token, balance in zip(tokens, balances):
		print(token + "\t" + str(balance));
	print();
	print("Last change block:", lastChangeBlock)


def getProtocolFeesCollector():
    protocolFeesCollector = BAL.balVaultGetProtocolFeesCollector()
    print("Protocol fees collector:", protocolFeesCollector)

	
def hasApprovedRelayer():
    hasApprovedRelayer = BAL.balVaultHasApprovedRelayer(USER, USER)
    print("Has approved relayer:", hasApprovedRelayer)


if __name__ == '__main__':
	functions = [WETH, getAuthorizer, getPool, getPoolTokenInfo, getPoolTokens, getProtocolFeesCollector, hasApprovedRelayer]
	print("General Vault Information")
	print("Pool used", POOLID)
	print("Token used", TOKENADDRESS)
	print("User used", USER)
	print()
	for function in functions:
		print("==============================================")
		print("Information for function:", function.__name__)
		function()
		print()
