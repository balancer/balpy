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
	gas_speed_approval = "fast";
	gas_speed_trade = "fast";

	bal = balpy.balpy.balpy(data["network"]);
	swap = data["batchSwap"];
	is_flash_swap = bal.balSwapIsFlashSwap(swap);

	print();
	print("==============================================================")
	print("================ Step 1: Check Token Balances ================")
	print("==============================================================")
	print();
	
	tokens = swap["assets"];
	amounts_in = swap["limits"];
	if not is_flash_swap:
		if not bal.erc20HasSufficientBalances(tokens, amounts_in):
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

	if not is_flash_swap:
		bal.erc20AsyncEnforceSufficientVaultAllowances(tokens, amounts_in, amounts_in, gas_factor, gas_speed_approval);
	else:
		print("Executing Flash Swap, no token approvals necessary.")
	# quit();

	print();
	print("==============================================================")
	print("=============== Step 3: Execute Batch Swap Txn ===============")
	print("==============================================================")
	print();

	tx_hash = bal.balDoBatchSwap(swap, gas_factor=gas_factor, gasPriceSpeed=gas_speed_trade);
	
if __name__ == '__main__':
	main();