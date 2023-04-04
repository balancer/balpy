import balpy
import sys
import os
import json
import jstyleson
import time

import webbrowser

def main():
	
	if len(sys.argv) < 2:
		print("Usage: python3", sys.argv[0], "/path/to/pool.json");
		quit();

	pathToPool = sys.argv[1];
	if not os.path.isfile(pathToPool):
		print("Path", pathToPool, "does not exist. Please enter a valid path.")
		quit();

	with open(pathToPool) as f:
		pool = jstyleson.load(f)

	bal = balpy.balpy.balpy(pool["network"]);
	gasFactor = 1.05;
	gasSpeed = pool["gasSpeed"];
	gasPriceGweiOverride = pool["gasPriceOverride"];
	if gasPriceGweiOverride == "":
		gasPriceGweiOverride = -1;
	gasPriceGweiOverride = float(gasPriceGweiOverride);

	print();
	print("==============================================================")
	print("================ Step 1: Check Token Balances ================")
	print("==============================================================")
	print();
	
	tokens = list(pool["tokens"].keys());
	initialBalances = [pool["tokens"][token]["initialBalance"] for token in tokens];
	if not bal.erc20HasSufficientBalances(tokens, initialBalances):
		print("Please fix your insufficient balance before proceeding.");
		print("Quitting...");
		quit();

	print();
	print("==============================================================")
	print("============== Step 2: Approve Token Allowance ==============")
	print("==============================================================")
	print();

	(tokensSorted, allowancesSorted) = bal.erc20GetTargetAllowancesFromPoolData(pool);
	initialBalancesSorted = [pool["tokens"][token]["initialBalance"] for token in tokensSorted];
	# Async: Do [Approve]*N then [Wait]*N instead of [Approve, Wait]*N
	bal.erc20AsyncEnforceSufficientVaultAllowances(tokensSorted, allowancesSorted, initialBalancesSorted, gasFactor, gasSpeed, gasPriceGweiOverride=gasPriceGweiOverride);

	print();
	print("==============================================================")
	print("=============== Step 3: Create Pool in Factory ===============")
	print("==============================================================")
	print();
	creationHash = None;
	if not "poolId" in pool.keys():
		txHash = bal.balCreatePoolInFactory(pool, gasFactor, gasSpeed, gasPriceGweiOverride=gasPriceGweiOverride);
		if not txHash:
			quit();
		poolId = bal.balGetPoolIdFromHash(txHash);
		creationHash = txHash;
		pool["poolId"] = poolId;
		with open(pathToPool, 'w') as f:
			json.dump(pool, f, indent=4);
	else:
		print("PoolId found in pool description. Skipping the pool factory!");
		poolId = pool["poolId"];

	poolLink = bal.balGetLinkToFrontend(poolId);
	if not poolLink == "":
		webbrowser.open_new_tab(poolLink);

	print();
	print("==================================================================")
	print("=============== Step 4: Add Initial Tokens to Pool ===============")
	print("==================================================================")
	print();
	try:
		time.sleep(5); # sleep ensure that the RPC knows the new pool exists
		txHash = bal.balJoinPoolInit(pool, poolId, gasPriceGweiOverride=gasPriceGweiOverride);
	except Exception as e:
		print("Joining pool failed!");
		print("Depending on the pool type, this could be due to you not being the pool owner");
		print("Caught exception:", e);
	quit();




	print();
	print("==================================================================")
	print("================== Step 5: Verify Pool Contract ==================")
	print("==================================================================")
	print();

	if not creationHash is None:
		command = bal.balGeneratePoolCreationArguments("0x" + poolId, creationHash=creationHash);
	else:
		command = bal.balGeneratePoolCreationArguments("0x" + poolId);

	print(command)
	print()
	print("If you need more complete instructions on what to do with this command, go to:");
	print("\thttps://dev.balancer.fi/resources/pools/verification");
	print()

if __name__ == '__main__':
	main();
