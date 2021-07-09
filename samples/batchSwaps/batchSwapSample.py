import balpy
import sys
import os
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
		data = json.load(f)

	gasFactor = 1.05;
	gasSpeedApproval = "fast";
	gasSpeedTrade = "fast";

	bal = balpy.balpy.balpy(data["network"]);
	swap = data["batchSwap"];
	isFlashSwap = bal.balSwapIsFlashSwap(swap);

	print();
	print("==============================================================")
	print("================ Step 1: Check Token Balances ================")
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
	print("============== Step 2: Approve Token Allowance ===============")
	print("==============================================================")
	print();

	if not isFlashSwap:
		bal.erc20AsyncEnforceSufficientVaultAllowances(tokens, amountsIn, amountsIn, gasFactor, gasSpeedApproval);
	else:
		print("Executing Flash Swap, no token approvals necessary.")
	# quit();

	print();
	print("==============================================================")
	print("=============== Step 3: Execute Batch Swap Txn ===============")
	print("==============================================================")
	print();

	txHash = bal.balDoBatchSwap(swap, gasFactor=gasFactor, gasPriceSpeed=gasSpeedTrade);
	
if __name__ == '__main__':
	main();