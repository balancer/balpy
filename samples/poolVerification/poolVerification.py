import balpy

from os.path import join, dirname
from dotenv import load_dotenv
# Load .env file
dotenv_path = join(dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

def main():
	network = "kovan"

	bal = balpy.balpy.balpy(network);
	poolId = "0x0910c350d5e836324491892d51bb4e97c33eaf23000200000000000000000357"
	command = bal.balGeneratePoolCreationArguments(poolId);
	
	print()
	print(command)
	print()

	print("If you need more complete instructions on what to do with this command, go to:");
	print("\thttps://dev.balancer.fi/resources/pools/verification");
	
if __name__ == '__main__':
	main();