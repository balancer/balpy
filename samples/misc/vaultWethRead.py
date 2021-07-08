import balpy

def main():
	network = "kovan"

	bal = balpy.balpy.balpy(network);
	weth = bal.balVaultWeth();
	print(weth);
		
if __name__ == '__main__':
	main();