import balpy

def main():
	network = "mainnet"

	bal = balpy.balpy.balpy(network);
	pool_id = "0x5c6ee304399dbdb9c8ef030ab642b10820db8f56000200000000000000000014"
	(tokens, balances, last_change_block) = bal.balVaultGetPoolTokens(pool_id);
	
	print("==============================================")
	print("Information for pool:")
	print("\t" + pool_id)
	print();
	print("\tToken\t\t\t\t\t\tBalance (wei)")
	print("\t-----\t\t\t\t\t\t-------------")
	for token, balance in zip(tokens, balances):
		print("\t" + token + "\t" + str(balance));
	print();
	print("\tLast change block:", last_change_block)
	print();
	
if __name__ == '__main__':
	main();