import balpy
import sys
import os
import jstyleson
import json

def main():
	
	if len(sys.argv) < 2:
		print("Usage: python3", sys.argv[0], "/path/to/join.json");
		quit();

	pathToJoin = sys.argv[1];
	if not os.path.isfile(pathToJoin):
		print("Path", pathToJoin, "does not exist. Please enter a valid path.")
		quit();

	with open(pathToJoin) as f:
		join = jstyleson.load(f)

	gasFactor = 1.05;
	gasSpeed = "average";
	gasPriceGweiOverride = -1; # -1 uses etherscan price at speed for gasSpeed, all other values will override
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
	(tokensSorted, allowancesSorted) = bal.erc20GetTargetAllowancesFromPoolData(join);
	amountsSorted = [join["tokens"][token]["amount"] for token in tokensSorted];
	
	# Async: Do [Approve]*N then [Wait]*N instead of [Approve, Wait]*N
	bal.erc20AsyncEnforceSufficientVaultAllowances(tokensSorted, allowancesSorted, amountsSorted, gasFactor, gasSpeed, gasPriceGweiOverride=gasPriceGweiOverride);

	print();
	print("===============================================================")
	print("================= Step 3: Send Tokens to Pool =================")
	print("===============================================================")
	print();

	query = False;
	output = bal.balJoinPool(join, query=query);

	if query:
		print("queryJoin results:")
		print(json.dumps(output,indent=4));

if __name__ == '__main__':
	main();
