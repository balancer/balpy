import balpy
import json

def main():
	
	network = "mainnet";
	poolId = "0x5c6ee304399dbdb9c8ef030ab642b10820db8f56000200000000000000000014";

	bal = balpy.balpy.balpy(network)

	print("Querying single pool", poolId)
	pool = bal.balApiGetPool(poolId);
	print(json.dumps(pool, indent=4))
	print()

	print("Querying all pools on", network)
	pools = bal.balApiGetPools();
	print(json.dumps(pools, indent=4))

if __name__ == '__main__':
	main();