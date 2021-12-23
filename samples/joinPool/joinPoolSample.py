import balpy
import sys
import os
import json

def main():
	
	if len(sys.argv) < 2:
		print("Usage: python3", sys.argv[0], "/path/to/join.json");
		quit();

	path_to_join = sys.argv[1];
	if not os.path.isfile(path_to_join):
		print("Path", path_to_join, "does not exist. Please enter a valid path.")
		quit();

	with open(path_to_join) as f:
		join = json.load(f)

	gas_factor = 1.05;
	gas_speed = "average";
	gas_price_gwei_override = -1; # -1 uses etherscan price at speed for gas_speed, all other values will override
	bal = balpy.balpy.balpy(join["network"]);

	print();
	print("==============================================================")
	print("================ Step 1: Check Token Balances ================")
	print("==============================================================")
	print();
	
	tokens = list(join["tokens"].keys());
	amounts = [join["tokens"][token]["amount"] for token in tokens];
	if not bal.erc20HasSufficientBalances(tokens, amounts):
		print("Please fix your insufficient balance before proceeding.")
		print("Quitting...")
		quit();

	print();
	print("===============================================================")
	print("=============== Step 2: Approve Token Allowance ===============")
	print("===============================================================")
	print();

	#the poolData structure is similar to joinData. Will be renamed in the future.
	(tokens_sorted, allowances_sorted) = bal.erc20GetTargetAllowancesFromPoolData(join);
	amounts_sorted = [join["tokens"][token]["amount"] for token in tokens_sorted];
	
	# Async: Do [Approve]*N then [Wait]*N instead of [Approve, Wait]*N
	bal.erc20AsyncEnforceSufficientVaultAllowances(tokens_sorted, allowances_sorted, amounts_sorted, gas_factor, gas_speed, gas_price_gwei_override=gas_price_gwei_override);

	print();
	print("===============================================================")
	print("================= Step 3: Send Tokens to Pool =================")
	print("===============================================================")
	print();

	tx_hash = bal.balJoinPoolExactIn(join, gas_price_gwei_override=gas_price_gwei_override);

if __name__ == '__main__':
	main();
