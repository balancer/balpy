import balpy

def main():
	gas_factor = 1.05;
	gas_speed = "fast";
	gas_override = 5;

	network = "kovan"
	bal = balpy.balpy.balpy(network);
	allowed_address = bal.deploymentAddresses["Vault"];
	tokens = [	"0xdFCeA9088c8A88A76FF74892C1457C17dfeef9C1",
				"0x41286Bb1D3E870f3F750eB7E1C25d7E48c8A1Ac7",
				"0xc2569dd7d0fd715B054fBf16E75B001E5c0C1115",
				"0xAf9ac3235be96eD496db7969f60D354fe5e426B0",
				"0x04DF6e4121c27713ED22341E7c7Df330F56f289B",
				"0x8F4beBF498cc624a0797Fe64114A6Ff169EEe078",
				"0x1C8E3Bcb3378a443CC591f154c5CE0EBb4dA9648",
				"0xcC08220af469192C53295fDd34CFb8DF29aa17AB",
				"0x15E76Fc74C6ab1c3141D61219883d1c59F716E21",
				"0x22ee6c3B011fACC530dd01fe94C58919344d6Db5"];

	nonce = bal.web3.eth.get_transaction_count(bal.web3.eth.default_account);
	hashes = [];

	for token in tokens:
		print("Checking:", token)
		allowance = bal.erc20GetAllowanceStandard(token, allowed_address);
		if allowance > 0:
			tx_hash = bal.erc20SignAndSendNewAllowance(	token,
														allowed_address,
														0,
														gas_factor,
														gas_speed,
														nonceOverride=nonce,
														isAsync=True,
														gasPriceGweiOverride=gas_override);
			nonce += 1
			hashes.append(tx_hash);
			print("\tRevoking allowance -- tx_hash:", tx_hash)
		else:
			print("\tNo allowance. Skipping...")

	for tx_hash in hashes:
		bal.waitForTx(tx_hash);
		
if __name__ == '__main__':
	main();