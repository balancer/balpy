import balpy
import sys
import os
import jstyleson
import json

def main():
	
	if len(sys.argv) < 2:
		print("Usage: python3", sys.argv[0], "/path/to/swap.json");
		quit();

	pathToSwap = sys.argv[1];
	if not os.path.isfile(pathToSwap):
		print("Path", pathToSwap, "does not exist. Please enter a valid path.")
		quit();

	with open(pathToSwap) as f:
		data = jstyleson.load(f)

	gasFactor = 1.05;
	gasSpeedApproval = "fast";
	gasSpeedTrade = "fast";


	bal = balpy.balpy.balpy(data["network"]);
	
	print();
	print("==============================================================")
	print("============== Step 1: Query Smart Order Router ==============")
	print("==============================================================")
	print();
	sor_result = bal.balSorQuery(data)
	swap = sor_result["batchSwap"];

	isFlashSwap = bal.balSwapIsFlashSwap(swap);

	print();
	print("==============================================================")
	print("================ Step 2: Check Token Balances ================")
	print("==============================================================")
	print();
	
	tokens = swap["assets"];
	amountsIn = swap["limits"];
	if not isFlashSwap:
		if not bal.erc20HasSufficientBalances(tokens, amountsIn):
			print("Please fix your insufficient balance before proceeding.")
			print("Quitting...")
			quit();
	else:
		print("Executing Flash Swap, no token balances necessary.")


	print();
	print("==============================================================")
	print("============== Step 3: Approve Token Allowance ===============")
	print("==============================================================")
	print();

	if not isFlashSwap:
		bal.erc20AsyncEnforceSufficientVaultAllowances(tokens, amountsIn, amountsIn, gasFactor, gasSpeedApproval);
	else:
		print("Executing Flash Swap, no token approvals necessary.")
	# quit();

	print();
	print("==============================================================")
	print("=============== Step 4: Execute Batch Swap Txn ===============")
	print("==============================================================")
	print();

	txHash = bal.balDoBatchSwap(swap, gasFactor=gasFactor, gasPriceSpeed=gasSpeedTrade);
	
if __name__ == '__main__':
	main();