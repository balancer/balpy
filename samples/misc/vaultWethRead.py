import balpy

def main():
	network = "polygon"

	bal = balpy.balpy.balpy(network);
	weth = bal.balVaultWeth();
	print(weth);
		
if __name__ == '__main__':
	main();