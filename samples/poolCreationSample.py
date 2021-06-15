import balpy
import sys
import os
import json

def main():
	
	if len(sys.argv) < 2:
		print("Usage: python3", sys.argv[0], "/path/to/pool.json");
		quit();

	pathToPool = sys.argv[1];
	if not os.path.isfile(pathToPool):
		print("Path", pathToPool, "does not exist. Please enter a valid path.")
		quit();

	with open(pathToPool) as f:
		pool = json.load(f)

	gasFactor = 1.05;
	gasSpeedApproval = "fast";

	# bal = balpy.balpy(pool["network"]);
	bal = balpy.balpy.balpy(pool["network"]);

	# verify weights
	if not bal.balWeightsEqualOne(pool):
		quit();

	print();
	print("==============================================================")
	print("================ Step 1: Check Token Balances ================")
	print("==============================================================")
	print();
	
	if not bal.erc20HasSufficientBalances(pool):
		print("Please fix your insufficient balance before proceeding.")
		print("Quitting...")
		quit();

	print();
	print("==============================================================")
	print("============== Step 2: Approve Token Allowance ==============")
	print("==============================================================")
	print();

	# Async: Do [Approve]*N then [Wait]*N instead of [Approve, Wait]*N
	bal.erc20AsyncEnforceSufficientVaultAllowances(pool, gasFactor, gasSpeedApproval);

	print();
	print("==============================================================")
	print("=============== Step 3: Create Pool in Factory ===============")
	print("==============================================================")
	print();

	if not "poolId" in pool.keys():
		txHash = bal.balCreatePoolInFactory("WeightedPoolFactory", pool, gasFactor, gasSpeedApproval, gasPriceGweiOverride=6);
		poolId = bal.balGetPoolIdFromHash(txHash);
		pool["poolId"] = poolId;
		with open(pathToPool, 'w') as f:
			json.dump(pool, f, indent=4)
	else:
		print("PoolId found in pool description. Skipping the pool factory!")
		poolId = pool["poolId"];
	
	print();
	print("==============================================================")
	print("=============== Step 4: Register Pool in Vault ===============")
	print("==============================================================")
	print();

	txHash = bal.balRegisterPoolWithVault(pool, poolId, gasPriceGweiOverride=7)

if __name__ == '__main__':
	main();