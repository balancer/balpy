import balpy

def main():
	network = "kovan"

	bal = balpy.balpy.balpy(network);
	pool_id = "0x6b15a01b5d46a5321b627bd7deef1af57bc629070000000000000000000000d4";
	(value, is_updating, precision) = bal.balStablePoolGetAmplificationParameter(pool_id);
	print("value:", value)
	print("is_updating:", is_updating)
	print("precision:", precision)
		
if __name__ == '__main__':
	main();