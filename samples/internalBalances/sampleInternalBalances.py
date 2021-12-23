import balpy

def print_balances(bal, tokens, address=None):
	if not address is None:
		print("Balances for", address);
	print("Token\t\t\t\t\t\tInternal Balance\tExternal Balance")
	internal_balances = bal.balVaultGetInternalBalance(tokens, address);
	for token in internal_balances.keys():
		internal = internal_balances[token];
		external = bal.erc20GetBalanceStandard(token, address);
		print(token, "\t", '{:.18f}'.format(internal), "\t", '{:.18f}'.format(external))
	print();

def main():
	network = "kovan"
	bal = balpy.balpy.balpy(network);

	dead_address = "0x0000000000000000000000000000000000000000";

	gas_factor = 1.05;
	gas_price_speed = "average";
	tokens = ["0xdFCeA9088c8A88A76FF74892C1457C17dfeef9C1"];
	amounts = [10.0];
	allowances = [-1];
	
	token = tokens[0];

	# enforce allowance
	bal.erc20AsyncEnforceSufficientVaultAllowances(tokens, allowances, amounts, gas_factor, gas_price_speed);
	
	# QUERY INTERNAL BALANCE(S)
	internal_balances = bal.balVaultGetInternalBalance(tokens);

	# DEPOSIT_INTERNAL
	print();
	print("==============================================================");
	print("================ Deposit to Internal Balances ================");
	print("==============================================================");
	print();
	
	print("\n==================== Starting Balances ====================\n");
	print_balances(bal, tokens);

	amount = 10.0;
	print("Depositing", amount, "of token", token, "to internal balance...");
	bal.balVaultDoManageUserBalance( bal.UserBalanceOpKind["DEPOSIT_INTERNAL"], token, amount, bal.address, bal.address);
	
	print("\n==================== Ending Balances ====================\n");
	print_balances(bal, tokens);

	# WITHDRAW_INTERNAL	= 1;
	print();
	print("=============================================================");
	print("============== Withdraw from Internal Balances ==============");
	print("=============================================================");
	print();
	
	print("\n==================== Starting Balances ====================\n");
	print_balances(bal, tokens);

	amount = 5.0;
	print("Withdrawing", amount, "of token", token, "from internal balance...\n");
	bal.balVaultDoManageUserBalance( bal.UserBalanceOpKind["WITHDRAW_INTERNAL"], token, amount, bal.address, bal.address);
	
	print("\n==================== Ending Balances ====================\n");
	print_balances(bal, tokens);


	# TRANSFER_INTERNAL	= 2;
	print();
	print("============================================================");
	print("============== Transferring Internal Balances ==============");
	print("============================================================");
	print();
	
	print("\n==================== Starting Balances ====================\n");
	print_balances(bal, tokens, bal.address);
	print_balances(bal, tokens, dead_address);

	amount = 2.5;
	print("Transferring", amount, "of token", token, "from", bal.address, "to", dead_address,"INTERNALLY\n");
	bal.balVaultDoManageUserBalance( bal.UserBalanceOpKind["TRANSFER_INTERNAL"], token, amount, bal.address, dead_address);
	
	print("\n==================== Ending Balances ====================\n");
	print_balances(bal, tokens, bal.address);
	print_balances(bal, tokens, dead_address);

	# TRANSFER_EXTERNAL	= 3;
	print();
	print("============================================================");
	print("============== Transferring External Balances ==============");
	print("============================================================");
	print();
	
	print("\n==================== Starting Balances ====================\n");
	print_balances(bal, tokens, bal.address);
	print_balances(bal, tokens, dead_address);

	amount = 1.25;
	print("Transferring", amount, "of token", token, "from", bal.address, "to", dead_address,"EXTERNALLY\n");
	bal.balVaultDoManageUserBalance( bal.UserBalanceOpKind["TRANSFER_EXTERNAL"], token, amount, bal.address, dead_address);
	
	print("\n==================== Ending Balances ====================\n");
	print_balances(bal, tokens, bal.address);
	print_balances(bal, tokens, dead_address);

if __name__ == '__main__':
	main();