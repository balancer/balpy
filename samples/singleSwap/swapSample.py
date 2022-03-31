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
	gasSpeedApproval = "average";
	gasSpeedTrade = "average";

	bal = balpy.balpy.balpy(data["network"]);
	swap = data["swap"];

	# determine the necessary allowance based on swap kind
	maxSend = None;
	kind = int(swap["kind"])
	if kind == 0: #GIVEN_IN
		maxSend = swap["amount"];
	elif kind == 1: #GIVEN_OUT
		maxSend = swap["limit"]


	print();
	print("==============================================================")
	print("================ Step 1: Check Token Balances ================")
	print("==============================================================")
	print();
	
	tokens = [swap["assetIn"]];
	amountIn = [maxSend];
	if not bal.erc20HasSufficientBalances(tokens, amountIn):
		print("Please fix your insufficient balance before proceeding.")
		print("Quitting...")
		quit();

	print();
	print("==============================================================")
	print("============== Step 2: Approve Token Allowance ===============")
	print("==============================================================")
	print();

	bal.erc20AsyncEnforceSufficientVaultAllowances(tokens, amountIn, amountIn, gasFactor, gasSpeedApproval);

	print();
	print("==============================================================")
	print("================== Step 3: Execute Swap Txn ==================")
	print("==============================================================")
	print();

	txHash = bal.balDoSwap(swap, gasFactor=gasFactor, gasPriceSpeed=gasSpeedTrade);
	
if __name__ == '__main__':
	main();