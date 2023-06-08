# import graph
import sys
import balpy.graph.graph as balGraph

def main():
	
	batch_size = 100;
	print();

	if len(sys.argv) < 2:
		print("Usage: python", sys.argv[0], "<network>");
		print("No network given; defaulting to mainnet Ethereum")
		network = "mainnet"
	else:
		network = sys.argv[1];
	
	networks = ["mainnet", "kovan", "polygon"];

	if not network in networks:
		print("Network", network, "is not supported!");
		print("Supported networks are:");
		for n in networks:
			print("\t" + n);
		print("Quitting")
		quit();

	verbose = True;
	bg = balGraph.TheGraph(network)
	pools = bg.getV2Pools(batch_size, verbose=verbose)
	bg.printJson(pools)

if __name__ == '__main__':
	main();
