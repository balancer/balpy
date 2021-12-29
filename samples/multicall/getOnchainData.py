import balpy
import json
import requests
import time

def main():
	network = "mainnet";
	bal = balpy.balpy.balpy(network);

	pool_ids_url = "https://raw.githubusercontent.com/gerrrg/balancer-pool-ids/master/pools/" + network + ".json";
	r = requests.get(pool_ids_url);
	pool_ids = r.json()["pools"];

	if "Element" in pool_ids.keys():
		del pool_ids["Element"];

	t_start = time.time();
	results = bal.getOnchainData(pool_ids);
	t_end = time.time();
	print("Query took", t_end - t_start, "seconds");

	print(json.dumps(results,indent=4));

if __name__ == '__main__':
	main();