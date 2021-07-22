import balpy

def main():
	network = "kovan"

	bal = balpy.balpy.balpy(network);
	weth = bal.balVaultWeth();
	print("Wrapped ETH Address:", weth);
		
if __name__ == '__main__':
	main();