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
	swap = data["singleSwap"];

	print();
	print("=============================================================")
	print("================ Step 1: Check Token Balance ================")
	print("=============================================================")
	print();
	
	if swap["kind"] == "0" and not bal.erc20HasSufficientBalance(swap["assetIn"], swap["amount"]):
		print("Please fix your insufficient balance before proceeding.")
		print("Quitting...")
		quit();


	print();
	print("==============================================================")
	print("============== Step 2: Approve Token Allowance ===============")
	print("==============================================================")
	print();

	if swap["kind"] == "0" and not bal.erc20AsyncEnforceSufficientVaultAllowance(swap["assetIn"], swap["amount"], swap["amount"], gasFactor, gasSpeedApproval):
		print("Please fix your insufficient token allowance before proceeding.")
		print("Quitting...")
		quit();

	print();
	print("===============================================================")
	print("=============== Step 3: Execute Single Swap Txn ===============")
	print("===============================================================")
	print();

	txHash = bal.balDoSingleSwap(data, gasFactor=gasFactor, gasPriceSpeed=gasSpeedTrade);
	
if __name__ == '__main__':
	main();