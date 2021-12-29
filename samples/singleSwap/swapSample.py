import balpy
import sys
import os
import json

def main():
	
	if len(sys.argv) < 2:
		print("Usage: python3", sys.argv[0], "/path/to/swap.json");
		quit();

	path_to_swap = sys.argv[1];
	if not os.path.isfile(path_to_swap):
		print("Path", path_to_swap, "does not exist. Please enter a valid path.")
		quit();

	with open(path_to_swap) as f:
		data = json.load(f)

	gas_factor = 1.05;
	gas_speed_approval = "average";
	gas_speed_trade = "average";

	bal = balpy.balpy.balpy(data["network"]);
	swap = data["swap"];

	# determine the necessary allowance based on swap kind
	max_send = None;
	kind = int(swap["kind"])
	if kind == 0: #GIVEN_IN
		max_send = swap["amount"];
	elif kind == 1: #GIVEN_OUT
		max_send = swap["limit"]


	print();
	print("==============================================================")
	print("================ Step 1: Check Token Balances ================")
	print("==============================================================")
	print();
	
	tokens = [swap["assetIn"]];
	amount_in = [max_send];
	if not bal.erc20HasSufficientBalances(tokens, amount_in):
		print("Please fix your insufficient balance before proceeding.")
		print("Quitting...")
		quit();

	print();
	print("==============================================================")
	print("============== Step 2: Approve Token Allowance ===============")
	print("==============================================================")
	print();

	bal.erc20AsyncEnforceSufficientVaultAllowances(tokens, amount_in, amount_in, gas_factor, gas_speed_approval);

	print();
	print("==============================================================")
	print("=============== Step 3: Execute Batch Swap Txn ===============")
	print("==============================================================")
	print();

	tx_hash = bal.balDoSwap(swap, gas_factor=gas_factor, gasPriceSpeed=gas_speed_trade);
	
if __name__ == '__main__':
	main();