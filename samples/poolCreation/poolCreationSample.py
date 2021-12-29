import balpy
import sys
import os
import json
import jstyleson

import webbrowser

def main():
	
	if len(sys.argv) < 2:
		print("Usage: python3", sys.argv[0], "/path/to/pool.json");
		quit();

	path_to_pool = sys.argv[1];
	if not os.path.isfile(path_to_pool):
		print("Path", path_to_pool, "does not exist. Please enter a valid path.")
		quit();

	with open(path_to_pool) as f:
		pool = jstyleson.load(f)

	bal = balpy.balpy.balpy(pool["network"]);
	gas_factor = 1.05;
	gas_speed = pool["gas_speed"];
	gas_price_gwei_override = pool["gasPriceOverride"];
	if gas_price_gwei_override == "":
		gas_price_gwei_override = -1;
	gas_price_gwei_override = float(gas_price_gwei_override);

	print();
	print("==============================================================")
	print("================ Step 1: Check Token Balances ================")
	print("==============================================================")
	print();
	
	tokens = list(pool["tokens"].keys());
	initial_balances = [pool["tokens"][token]["initialBalance"] for token in tokens];
	if not bal.erc20HasSufficientBalances(tokens, initial_balances):
		print("Please fix your insufficient balance before proceeding.");
		print("Quitting...");
		quit();

	print();
	print("==============================================================")
	print("============== Step 2: Approve Token Allowance ==============")
	print("==============================================================")
	print();

	(tokens_sorted, allowances_sorted) = bal.erc20GetTargetAllowancesFromPoolData(pool);
	initial_balances_sorted = [pool["tokens"][token]["initialBalance"] for token in tokens_sorted];
	# Async: Do [Approve]*N then [Wait]*N instead of [Approve, Wait]*N
	bal.erc20AsyncEnforceSufficientVaultAllowances(tokens_sorted, allowances_sorted, initial_balances_sorted, gas_factor, gas_speed, gas_price_gwei_override=gas_price_gwei_override);

	print();
	print("==============================================================")
	print("=============== Step 3: Create Pool in Factory ===============")
	print("==============================================================")
	print();
	creation_hash = None;
	if not "pool_id" in pool.keys():
		tx_hash = bal.balCreatePoolInFactory(pool, gas_factor, gas_speed, gas_price_gwei_override=gas_price_gwei_override);
		if not tx_hash:
			quit();
		pool_id = bal.balGetPoolIdFromHash(tx_hash);
		creation_hash = tx_hash;
		pool["pool_id"] = pool_id;
		with open(path_to_pool, 'w') as f:
			json.dump(pool, f, indent=4);
	else:
		print("PoolId found in pool description. Skipping the pool factory!");
		pool_id = pool["pool_id"];

	pool_link = bal.balGetLinkToFrontend(pool_id);
	if not pool_link == "":
		webbrowser.open_new_tab(pool_link);

	print();
	print("==================================================================")
	print("=============== Step 4: Add Initial Tokens to Pool ===============")
	print("==================================================================")
	print();
	try:
		tx_hash = bal.balJoinPoolInit(pool, pool_id, gas_price_gwei_override=gas_price_gwei_override);
	except:
		print("Joining pool failed! Are you the owner?");

	print();
	print("==================================================================")
	print("================== Step 5: Verify Pool Contract ==================")
	print("==================================================================")
	print();

	if not creation_hash is None:
		command = bal.balGeneratePoolCreationArguments("0x" + pool_id, creation_hash=creation_hash);
	else:
		command = bal.balGeneratePoolCreationArguments("0x" + pool_id);

	print(command)
	print()
	print("If you need more complete instructions on what to do with this command, go to:");
	print("\thttps://dev.balancer.fi/resources/pools/verification");
	print()

if __name__ == '__main__':
	main();
