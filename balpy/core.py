# core.py

# python basics
import json
import os
import requests
import time
import sys
import pkgutil
from decimal import *
import multiprocessing

# web3 
from web3 import Web3, middleware
from web3.gas_strategies.time_based import glacial_gas_price_strategy, slow_gas_price_strategy, medium_gas_price_strategy, fast_gas_price_strategy
from web3.middleware import geth_poa_middleware
from web3._utils.abi import get_abi_output_types

import eth_abi
from multicall.constants import MULTICALL_ADDRESSES
from . import balancerErrors as be

def process_data(thread_id, endpoint, input_data, output_abi_data, return_dict):
	output_abis = output_abi_data;
	w3 = Web3(Web3.HTTPProvider(endpoint))
	decoded_output_data_blocks = [];
	for od_bytes, pidAndFn in input_data:
		decoder = pidAndFn[1];
		decoded_output_data = w3.codec.decode_abi(output_abis[decoder], od_bytes);
		decoded_output_data_blocks.append(decoded_output_data);
	return_dict[thread_id] = decoded_output_data_blocks;

class Balpy(object):
	
	"""
	Balancer Protocol Python API
	Interface with Balancer V2 Smart contracts directly from Python
	"""

	DELEGATE_OWNER =	'0xBA1BA1ba1BA1bA1bA1Ba1BA1ba1BA1bA1ba1ba1B';
	ZERO_ADDRESS =  	'0x0000000000000000000000000000000000000000';

	# Constants
	INFINITE = 2 ** 256 - 1; #for infinite unlock

	# Environment variable names
	env_var_etherscan = 	"KEY_API_ETHERSCAN";
	env_var_infura = 		"KEY_API_INFURA";
	env_var_private = 	"KEY_PRIVATE";
	env_var_custom_rpc = 	"BALPY_CUSTOM_RPC";
	
	# Etherscan API call management	
	last_etherscan_call_time = 0;
	etherscan_max_rate = 5.0; #hz
	etherscan_speed_dict = {
			"slow":"SafeGasPrice",
			"average":"ProposeGasPrice",
			"fast":"FastGasPrice"
	};
	speed_dict = {
			"glacial":glacial_gas_price_strategy,
			"slow":slow_gas_price_strategy,
			"average":medium_gas_price_strategy,
			"fast":fast_gas_price_strategy
	}

	# Network parameters
	network_params = {
						"mainnet":	{"id":1,		"blockExplorerUrl":"etherscan.io",					"balFrontend":"app.balancer.fi/#/"		},
						"ropsten":	{"id":3,		"blockExplorerUrl":"ropsten.etherscan.io"													},
						"rinkeby":	{"id":4,		"blockExplorerUrl":"rinkeby.etherscan.io"													},
						"goerli":	{"id":5,		"blockExplorerUrl":"goerli.etherscan.io"													},
						"kovan":	{"id":42,		"blockExplorerUrl":"kovan.etherscan.io",			"balFrontend":"kovan.balancer.fi/#/"	},
						"polygon":	{"id":137,		"blockExplorerUrl":"polygonscan.com",				"balFrontend":"polygon.balancer.fi/#/"	},
						"fantom":	{"id":250,		"blockExplorerUrl":"ftmscan.com",					"balFrontend":"app.beets.fi/#/"			},
						"arbitrum":	{"id":42161,	"blockExplorerUrl":"arbiscan.io",					"balFrontend":"arbitrum.balancer.fi/#/"	}
					};

	# ABIs and Deployment Addresses
	abis = {};
	deployment_addresses = {};
	contract_directories = {
							"Vault": {
								"directory":"20210418-vault"
							},
							"BalancerHelpers": {
								"directory":"20210418-vault"
							},
							"WeightedPoolFactory": {
								"directory":"20210418-weighted-pool"
							},
							"WeightedPool2TokensFactory": {
								"directory":"20210418-weighted-pool"
							},
							"StablePoolFactory": {
								"directory":"20210624-stable-pool"
							},
							"LiquidityBootstrappingPoolFactory": {
								"directory":"20210721-liquidity-bootstrapping-pool"
							},
							"MetaStablePoolFactory": {
								"directory":"20210727-meta-stable-pool"
							},
							"InvestmentPoolFactory": {
								"directory":"20210907-investment-pool"
							},
							"Authorizer": {
								"directory":"20210418-authorizer"
							},
							"StablePhantomPoolFactory": {
								"directory":"testnet-linear-phantom-stable-pools"
							},
							"LinearPoolFactory": {
								"directory":"testnet-linear-phantom-stable-pools"
							}
						};

	decimals = {};
	erc20_contracts = {};

	user_balance_op_kind = {
		"DEPOSIT_INTERNAL":0,
		"WITHDRAW_INTERNAL":1,
		"TRANSFER_INTERNAL":2,
		"TRANSFER_EXTERNAL":3
	};
	inverse_user_balance_op_kind = {
		0:"DEPOSIT_INTERNAL",
		1:"WITHDRAW_INTERNAL",
		2:"TRANSFER_INTERNAL",
		3:"TRANSFER_EXTERNAL"
	};
	join_kind = {
		"INIT": 0,
		"EXACT_TOKENS_IN_FOR_BPT_OUT": 1,
		"TOKEN_IN_FOR_EXACT_BPT_OUT": 2
	}
	exit_kind = {
		"EXACT_BPT_IN_FOR_ONE_TOKEN_OUT": 0,
		"EXACT_BPT_IN_FOR_TOKENS_OUT": 1,
		"BPT_IN_FOR_EXACT_TOKENS_OUT": 2
	}

	def __init__(self, network=None, verbose=True, custom_config_file=None):
		super(Balpy, self).__init__();

		self.verbose = verbose;
		if self.verbose:
			print();
			print("==============================================================");
			print("============== Initializing Balancer Python API ==============");
			print("==============================================================");
			print();

		if network is None:
			print("No network set. Defaulting to kovan");
			network = "kovan";
		else:
			print("Network is set to", network);
		self.network = network.lower();

		# set high decimal precision
		getcontext().prec = 28;

		self.infura_api_key = 		os.environ.get(self.env_var_infura);
		self.custom_rpc = 			os.environ.get(self.env_var_custom_rpc);
		self.etherscan_api_key = 		os.environ.get(self.env_var_etherscan);
		self.private_key =  			os.environ.get(self.env_var_private);

		if self.infura_api_key is None and self.custom_rpc is None:
			self.ERROR("You need to add your KEY_API_INFURA or BALPY_CUSTOM_RPC environment variables\n");
			self.ERROR("!! If you are using L2, you must use BALPY_CUSTOM_RPC !!");
			print("\t\texport " + self.env_var_infura + "=<yourInfuraApiKey>");
			print("\t\t\tOR")
			print("\t\texport " + self.env_var_custom_rpc + "=<yourCustomRPC>");
			print("\n\t\tNOTE: if you set " + self.env_var_custom_rpc + ", it will override your Infura API key!")
			quit();

		if self.etherscan_api_key is None or self.private_key is None:
			self.ERROR("You need to add your keys to the your environment variables");
			print("\t\texport " + self.env_var_etherscan + "=<yourEtherscanApiKey>");
			print("\t\texport " + self.env_var_private + "=<yourPrivateKey>");
			quit();

		endpoint = self.custom_rpc;
		if endpoint is None:
			endpoint = 'https://' + self.network + '.infura.io/v3/' + self.infura_api_key;

		self.endpoint = endpoint;
		self.web3 = Web3(Web3.HTTPProvider(endpoint));
		acct = self.web3.eth.account.privateKeyToAccount(self.private_key);
		self.web3.eth.default_account = acct.address;
		self.address = acct.address;

		# initialize gas block caches
		self.curr_gas_price_speed = None;
		self.web3.middleware_onion.add(middleware.time_based_cache_middleware)
		self.web3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
		self.web3.middleware_onion.add(middleware.simple_cache_middleware)

		# add support for PoA chains
		self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)

		if self.verbose:
			print("Initialized account", self.web3.eth.default_account);
			print("Connected to web3 at", endpoint);

		using_custom_config = (not custom_config_file is None);
		custom_config = None;
		if using_custom_config:

			# load custom config file if it exists, quit if not
			if not os.path.isfile(custom_config_file):
				bal.ERROR("Custom config file" + custom_config_file + " not found!");
				quit();
			else:
				with open(custom_config_file,'r') as f:
					custom_config = json.load(f);
			# print(json.dumps(custom_config, indent=4))

			# ensure all required fields are in the custom_config
			required_fields = ["contracts", "networkParams"]
			has_all_requirements = True;
			for req in required_fields:
				if not req in custom_config.keys():
					has_all_requirements = False;
			if not has_all_requirements:
				bal.ERROR("Not all custom fields are in the custom config!");
				print("You must include:");
				for req in required_fields:
					print("\t"+req);
				print();
				quit();

			# add network params for network
			curr_network_params = {
				"id":				custom_config["networkParams"]["id"],
				"blockExplorerUrl":	custom_config["networkParams"]["blockExplorerUrl"]
			}

			if "balFrontend" in custom_config["networkParams"].keys():
				curr_network_params["balFrontend"] = custom_config["networkParams"]["balFrontend"];
			self.network_params[self.network] = curr_network_params;

		for contract_type in self.contract_directories.keys():
			subdir = self.contract_directories[contract_type]["directory"];

			# get contract abi from deployment
			abi_path = os.path.join('deployments', subdir , "abi", contract_type + '.json');
			try:
				f = pkgutil.get_data(__name__, abi_path).decode();
				curr_abi = json.loads(f);
				self.abis[contract_type] = curr_abi;
			except BaseException as error:
				self.ERROR('Error accessing file: {}'.format(abi_path))
				self.ERROR('{}'.format(error))

			# get deployment address for given network
			try:
				if using_custom_config:
					curr_address = custom_config["contracts"][contract_type];
				else:
					deployment_path = os.path.join('deployments', subdir, "output", self.network + '.json');
					f = pkgutil.get_data(__name__, deployment_path).decode();
					curr_data = json.loads(f);
					curr_address = self.web3.toChecksumAddress(curr_data[contract_type]);
				self.deployment_addresses[contract_type] = curr_address;
			except BaseException as error:
				self.WARN('{} not found for network {}'.format(contract_type, self.network))
				self.WARN('{}'.format(error))

		print("Available contracts on", self.network)
		for element in self.deployment_addresses.keys():
			address = self.deployment_addresses[element];
			print("\t" + address + "\t" + element)
		print();
		print("==============================================================");

	# ======================
	# ====Color Printing====
	# ======================
	def WARN(self, text):
		WARNING_BEGIN = '\033[93m';
		WARNING_END = '\033[0m';
		print(WARNING_BEGIN + "[WARNING] " + text + WARNING_END);

	def ERROR(self, text):
		ERROR_BEGIN = '\033[91m';
		ERROR_END = '\033[0m';
		print(ERROR_BEGIN + "[ERROR] " + text + ERROR_END);

	def GOOD(self, text):
		GOOD_BEGIN = '\033[92m'
		GOOD_END = '\033[0m';
		print(GOOD_BEGIN + text + GOOD_END);

	# =====================
	# ===Transaction Fns===
	# =====================
	def build_tx(self, fn, gas_factor, gas_speed="average", nonce_override=-1, gas_estimate_override=-1, gas_price_gwei_override=-1):
		chain_id_network = self.network_params[self.network]["id"];

		# Get nonce if not overridden
		if nonce_override > -1:
			nonce = nonce_override;
		else:
			nonce = self.web3.eth.get_transaction_count(self.web3.eth.default_account)

		# Calculate gas estimate if not overridden
		if gas_estimate_override > -1:
			gas_estimate = gas_estimate_override;
		else:
			try:
				gas_estimate = int(fn.estimateGas() * gas_factor);
			except BaseException as error:
				descriptive_error = be.handleException(error);
				self.ERROR("Transaction failed at gas estimation!");
				self.ERROR(descriptive_error);
				return(None);

		# Get gas price from Etherscan if not overridden
		if gas_price_gwei_override > -1:
			gas_price_gwei = gas_price_gwei_override;
		else:
			#rinkeby, kovan gas strategy
			if chain_id_network in [4, 42]:
				gas_price_gwei = 2;

			# polygon gas strategy
			elif chain_id_network == 137:
				gas_price_gwei = self.get_gas_price_polygon(gas_speed);

			#mainnet gas strategy
			else:
				gas_price_gwei = self.get_gas_price_etherscan_gwei(gas_speed);
		
		print("\tGas Estimate:\t", gas_estimate);
		print("\tGas Price:\t", gas_price_gwei, "Gwei");
		print("\tNonce:\t\t", nonce);

		# build transaction
		data = fn.buildTransaction({'chainId': chain_id_network,
								    'gas': gas_estimate,
								    'gasPrice': self.web3.toWei(gas_price_gwei, 'gwei'),
								    'nonce': nonce,
									});
		return(data);

	def send_tx(self, tx, is_async=False):
		signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key);
		tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction).hex();

		print();
		print("Sending transaction, view progress at:");
		print("\thttps://"+self.network_params[self.network]["blockExplorerUrl"]+"/tx/"+tx_hash);
		
		if not is_async:
			self.wait_for_tx(tx_hash);
		return(tx_hash);

	def wait_for_tx(self, tx_hash, time_out_sec=120):
		tx_successful = True;
		print();
		print("Waiting for tx:", tx_hash);
		try:
			receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=time_out_sec);
			if not receipt["status"] == 1:
				tx_successful = False;
		except BaseException as error:
			print('Transaction timeout: {}'.format(error))
			return(False);

		# Race condition: add a small delay to avoid getting the last nonce
		time.sleep(0.5);

		print("\tTransaction accepted by network!");
		if not tx_successful:
			self.ERROR("Transaction failed!")
			return(False)
		print("\tTransaction was successful!\n");

		return(True);

	def get_tx_receipt(self, tx_hash, delay, max_retries):
		for i in range(max_retries):
			try: 
				receipt = self.web3.eth.getTransactionReceipt(tx_hash);
				print("Retrieved receipt!");
				return(receipt);
			except Exception as e:
				print(e);
				print("Transaction not found yet, will check again in", delay, "seconds");
				time.sleep(delay);
		self.ERROR("Transaction not found in" + str(max_retries) + "retries.");
		return(False);

	# =====================
	# ====ERC20 methods====
	# =====================
	def erc20_get_contract(self, token_address):
		# Check to see if contract is already in cache
		if token_address in self.erc20_contracts.keys():
			return(self.erc20_contracts[token_address]);

		# Read files packaged in module
		abi_path = os.path.join('abi/ERC20.json');
		f = pkgutil.get_data(__name__, abi_path).decode();
		abi = json.loads(f);
		token = self.web3.eth.contract(self.web3.toChecksumAddress(token_address), abi=abi)
		self.erc20_contracts[token_address] = token;
		return(token);

	def erc20_get_decimals(self, token_address):
		if token_address in self.decimals.keys():
			return(self.decimals[token_address]);
		if token_address == self.ZERO_ADDRESS:
			self.decimals[token_address] = 18;
			return(18);
		token = self.erc20_get_contract(token_address);
		decimals = token.functions.decimals().call();
		self.decimals[token_address] = decimals;
		return(decimals);

	def erc20_get_balance_standard(self, token_address, address=None):
		if address is None:
			address = self.address;
		token = self.erc20_get_contract(token_address);
		decimals = self.erc20_get_decimals(token_address);
		standard_balance = Decimal(token.functions.balanceOf(address).call()) * Decimal(10**(-decimals));
		return(standard_balance);

	def erc20_get_allowance_standard(self, token_address, allowed_address):
		token = self.erc20_get_contract(token_address);
		decimals = self.erc20_get_decimals(token_address);
		standard_allowance = Decimal(token.functions.allowance(self.address,allowed_address).call()) * Decimal(10**(-decimals));
		return(standard_allowance);

	def erc20_build_function_set_allowance(self, token_address, allowed_address, allowance):
		token = self.erc20_get_contract(token_address);
		approve_function = token.functions.approve(allowed_address, allowance);
		return(approve_function);

	def erc20_sign_and_send_new_allowance(	self,
										token_address, 
										allowed_address, 
										allowance,
										gas_factor,
										gas_speed,
										nonce_override=-1, 
										gas_estimate_override=-1, 
										gas_price_gwei_override=-1,
										is_async=False):
		fn = self.erc20_build_function_set_allowance(token_address, allowed_address, allowance);
		tx = self.build_tx(fn, gas_factor, gas_speed, nonce_override, gas_estimate_override, gas_price_gwei_override);
		tx_hash = self.send_tx(tx, is_async);
		return(tx_hash);

	def erc20_has_sufficient_balance(self, token_address, amount_to_use):
		balance = self.erc20_get_balance_standard(token_address);

		print("Token:", token_address);
		print("\tNeed:", float(amount_to_use));
		print("\tWallet has:", float(balance));

		sufficient = (float(balance) >= float(amount_to_use));
		if not sufficient:
			self.ERROR("Insufficient Balance!");
		else:
			print("\tWallet has sufficient balance.");
		print();
		return(sufficient);
	
	def erc20_has_sufficient_balances(self, tokens, amounts):
		if not len(tokens) == len(amounts):
			self.ERROR("Array length mismatch with " + str(len(tokens)) + " tokens and " + str(len(amounts)) + " amounts.");
			return(False);
		num_elements = len(tokens);
		sufficient_balance = True;
		for i in range(num_elements):
			token = tokens[i];
			amount = amounts[i];
			current_has_sufficient_balance = self.erc20_has_sufficient_balance(token, amount);
			sufficient_balance &= current_has_sufficient_balance;
		return(sufficient_balance);

	def erc20_has_sufficient_allowance(self, token_address, allowed_address, amount):
		current_allowance = self.erc20_get_allowance_standard(token_address, allowed_address);
		balance = self.erc20_get_balance_standard(token_address);

		print("Token:", token_address);
		print("\tCurrent Allowance:", current_allowance);
		print("\tCurrent Balance:", balance);
		print("\tAmount to Spend:", amount);

		sufficient = (current_allowance >= Decimal(amount));

		if not sufficient:
			print("\tInsufficient allowance!");
			print("\tWill need to unlock", token_address);
		else:
			print("\tWallet has sufficient allowance.");
		print();
		return(sufficient);

	def erc20_enforce_sufficient_allowance(self,
										token_address,
										allowed_address,
										target_allowance,
										amount,
										gas_factor,
										gas_speed,
										nonce_override,
										gas_estimate_override,
										gas_price_gwei_override,
										is_async):
		if not self.erc20_has_sufficient_allowance(token_address, allowed_address, amount):
			if target_allowance == -1 or target_allowance == self.INFINITE:
				target_allowance = self.INFINITE;
			else:
				decimals = self.erc20_get_decimals(token_address);
				target_allowance = Decimal(target_allowance) * Decimal(10**decimals);
			target_allowance = int(target_allowance);
			print("Insufficient Allowance: Increasing to", target_allowance);
			tx_hash = self.erc20_sign_and_send_new_allowance(token_address, allowed_address, target_allowance, gas_factor, gas_speed, nonce_override=nonce_override, is_async=is_async, gas_price_gwei_override=gas_price_gwei_override);
			return(tx_hash);
		return(None);

	def erc20_enforce_sufficient_vault_allowance(self, token_address, target_allowance, amount, gas_factor, gas_speed, nonce_override=-1, gas_estimate_override=-1, gas_price_gwei_override=-1, is_async=False):
		return(self.erc20_enforce_sufficient_allowance(token_address, self.deployment_addresses["Vault"], target_allowance, amount, gas_factor, gas_speed, nonce_override, gas_estimate_override, gas_price_gwei_override, is_async));

	def erc20_get_target_allowances_from_pool_data(self, pool_description):
		(tokens, checksum_tokens) = self.bal_sort_tokens(list(pool_description["tokens"].keys()));
		allowances = [];
		for token in tokens:
			target_allowance = -1;
			if "allowance" in pool_description["tokens"][token].keys():
				target_allowance = pool_description["tokens"][token]["allowance"];
			if target_allowance == -1:
				target_allowance = self.INFINITE;
			allowances.append(target_allowance);
		return(tokens, allowances);

	def erc20_async_enforce_sufficient_vault_allowances(self, tokens, target_allowances, amounts, gas_factor, gas_speed, nonce_override=-1, gas_estimate_override=-1, gas_price_gwei_override=-1):
		if not len(tokens) == len(target_allowances):
			self.ERROR("Array length mismatch with " + str(len(tokens)) + " tokens and " + str(len(target_allowances)) + " target_allowances.");
			return(False);

		nonce = self.web3.eth.get_transaction_count(self.web3.eth.default_account);
		tx_hashes = [];
		num_elements = len(tokens);
		for i in range(num_elements):
			token = tokens[i];
			target_allowance = target_allowances[i];
			amount = amounts[i];
			tx_hash = self.erc20_enforce_sufficient_vault_allowance(token, target_allowance, amount, gas_factor, gas_speed, nonce_override=nonce, is_async=True);
			if not tx_hash is None:
				tx_hashes.append(tx_hash);
				nonce += 1;
		
		for tx_hash in tx_hashes:
			self.wait_for_tx(tx_hash)
		return(True)

	# =====================
	# ======Etherscan======
	# =====================
	def generate_etherscan_api_url(self):
		etherscan_url = self.network_params[self.network]["blockExplorerUrl"]
		separator = ".";
		if self.network in ["kovan", "rinkeby","goerli"]:
			separator = "-";
		url_front = "https://api" + separator + etherscan_url;
		return(url_front);

	def call_etherscan(self, url, max_retries=3, verbose=False):
		url_front = self.generate_etherscan_api_url();
		url = url_front + url + self.etherscan_api_key;
		if verbose:
			print("Calling:", url);

		count = 0;
		while count < max_retries:
			try:
				dt = (time.time() - self.last_etherscan_call_time);
				if dt < 1.0/self.etherscan_max_rate:
					time.sleep((1.0/self.etherscan_max_rate - dt) * 1.1);

				# faking a user-agent resolves the 403 (forbidden) errors on api-kovan.etherscan.io
				headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","DNT": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"};
				r = requests.get(url, headers=headers);
				if verbose:
					print("\t", r);
				self.last_etherscan_call_time = time.time();
				data = r.json();
				if verbose:
					print("\t", data);
				return(data);
			except Exception as e:
				print("Exception:", e);
				count += 1;
				delay_sec = 2;
				if verbose:
					self.WARN("Etherscan failed " + str(count) + " times. Retrying in " + str(delay_sec) + " seconds...");
				time.sleep(delay_sec);
		self.ERROR("Etherscan failed " + str(count) + " times.");
		return(False);

	def get_gas_price_etherscan_gwei(self, speed, verbose=False):
		if not speed in self.etherscan_speed_dict.keys():
			self.ERROR("Speed entered is:" + speed);
			self.ERROR("Speed must be one of the following options:");
			for s in self.etherscan_speed_dict.keys():
				print("\t" + s);
			return(False);

		url_string = "/api?module=gastracker&action=gasoracle&apikey=";# + self.etherscan_api_key;
		response = self.call_etherscan(url_string, verbose=verbose);
		return(response["result"][self.etherscan_speed_dict[speed]]);

	def get_transactions_by_address(self, address, internal=False, startblock=0, verbose=False):
		if verbose:
			print("\tQuerying data after block", startblock);

		internal_string = "";
		if internal:
			internal_string = "internal";

		etherscan_url = self.network_params[self.network]["blockExplorerUrl"]
		separator = ".";
		if self.network in ["kovan", "rinkeby","goerli"]:
			separator = "-";

		url = [];
		url.append("/api?module=account&action=txlist{}&address=".format(internal_string));
		url.append(address);
		url.append("&startblock={}&endblock=99999999&sort=asc&apikey=".format(startblock));
		url_string = "".join(url);
		txns = self.call_etherscan(url_string, verbose=verbose);

		if int(txns["status"]) == 0:
			self.ERROR("Etherscan query failed. Please try again.");
			return(False);
		elif int(txns["status"]) == 1:
			return(txns["result"]);

	def get_transaction_by_hash(self, tx_hash, verbose=False):
		url_string = "/api?module=proxy&action=eth_getTransactionByHash&txhash={}&apikey=".format(tx_hash);
		txns = self.call_etherscan(url_string, verbose=verbose);

		if verbose:
			print(txns)

		if txns == False:
			return(False);
		return(txns);

	def is_contract_verified(self, pool_id, verbose=False):
		address = self.bal_poold_id_to_address(pool_id);
		url = "/api?module=contract&action=getabi&address={}&apikey=".format(address);
		results = self.call_etherscan(url, verbose=verbose);
		if verbose:
			print(results);
		is_unverified = (results["result"] == "Contract source code not verified");
		return(not is_unverified);

	def get_gas_price_polygon(self, speed):
		if speed in self.etherscan_speed_dict.keys():
			etherscan_gas_speed_names_to_polygon = {
				"slow":"safeLow",
				"average":"standard",
				"fast":"fast"
			};
			speed = etherscan_gas_speed_names_to_polygon[speed];

		allowed_speeds = ["safeLow","standard","fast","fastest"];
		if speed not in allowed_speeds:
			self.ERROR("Speed entered is:" + speed);
			self.ERROR("Speed must be one of the following options:");
			for s in allowed_speeds:
				print("\t" + s);
			return(False);

		r = requests.get("https://gasstation-mainnet.matic.network/")
		prices = r.json();
		return(prices[speed]);

	def get_gas_price(self, speed):
		allowed_speeds = list(self.speed_dict.keys());
		if speed not in allowed_speeds:
			self.ERROR("Speed entered is:" + speed);
			self.ERROR("Speed must be one of the following options:");
			for s in allowed_speeds:
				print("\t" + s);
			return(False);

		if not speed == self.curr_gas_price_speed:
			self.curr_gas_price_speed = speed;
			self.web3.eth.set_gas_price_strategy(self.speed_dict[speed]);

		gas_price = self.web3.eth.generateGasPrice() * 1e-9;
		return(gas_price)

	def bal_sort_tokens(self, tokens_in):
		# tokens need to be sorted as lowercase, but if they're provided as checksum, then
		# the checksum format strings are still the keys outside of this function, so they
		# must be preserved as they're input
		lower_tokens = [t.lower() for t in tokens_in];
		lower_to_original = {};
		for i in range(len(tokens_in)):
			lower_to_original[lower_tokens[i]] = tokens_in[i];
		lower_tokens.sort();

		# get checksum tokens, translated sorted lower tokens back to their original format
		checksum_tokens = [self.web3.toChecksumAddress(t) for t in lower_tokens];
		sorted_input_tokens = [lower_to_original[f] for f in lower_tokens]

		return(sorted_input_tokens, checksum_tokens);

	def bal_weights_equal_one(self, pool_data):
		token_data = pool_data["tokens"];
		tokens = token_data.keys();
		
		weight_sum = Decimal(0.0);
		for token in tokens:
			weight_sum += Decimal(token_data[token]["weight"]);
		
		weight_equals_one = (weight_sum == Decimal(1.0));
		if not weight_equals_one:
			self.ERROR("Token weights add up to " + str(weight_sum) + ", but they must add up to 1.0");
			self.ERROR("If you are passing more than 16 digits of precision, you must pass the value as a string")
		return(weight_equals_one);

	def bal_convert_tokens_to_wei(self, tokens, amounts):
		raw_tokens = [];
		if not len(tokens) == len(amounts):
			self.ERROR("Array length mismatch with " + str(len(tokens)) + " tokens and " + str(len(amounts)) + " amounts.");
			return(False);
		num_elements = len(tokens);
		for i in range(num_elements):
			token = tokens[i];
			raw_value = amounts[i];
			decimals = self.erc20_get_decimals(token);
			raw = int(Decimal(raw_value) * Decimal(10**decimals));
			raw_tokens.append(raw);
		return(raw_tokens);

	def bal_get_factory_contract(self, pool_factory_name):
		address = self.deployment_addresses[pool_factory_name];
		abi = self.abis[pool_factory_name];
		factory = self.web3.eth.contract(address=address, abi=abi);
		return(factory);

	def bal_set_owner(self, pool_data):
		owner = self.ZERO_ADDRESS;
		if "owner" in pool_data.keys():
			owner_address = pool_data["owner"];
			if not len(owner_address) == 42:
				self.ERROR("Entry for \"owner\" must be a 42 character Ethereum address beginning with \"0x\"");
				return(False);
			owner = self.web3.toChecksumAddress(owner_address);
		return(owner);

	def bal_create_fn_weighted_pool_factory(self, pool_data):
		factory = self.bal_get_factory_contract("WeightedPoolFactory");
		(tokens, checksum_tokens) = self.bal_sort_tokens(list(pool_data["tokens"].keys()));

		int_with_decimals_weights = [int(Decimal(pool_data["tokens"][t]["weight"]) * Decimal(1e18)) for t in tokens];
		swap_fee_percentage = int(Decimal(pool_data["swapFeePercent"]) * Decimal(1e16));

		if not self.bal_weights_equal_one(pool_data):
			return(False);

		owner = self.bal_set_owner(pool_data);

		create_function = factory.functions.create(	pool_data["name"], 
													pool_data["symbol"], 
													checksum_tokens, 
													int_with_decimals_weights, 
													swap_fee_percentage, 
													owner);
		return(create_function);

	def bal_create_fn_weighted_pool2_tokens_factory(self, pool_data):
		factory = self.bal_get_factory_contract("WeightedPool2TokensFactory");
		(tokens, checksum_tokens) = self.bal_sort_tokens(list(pool_data["tokens"].keys()));
		
		if not len(tokens) == 2:
			self.ERROR("WeightedPool2TokensFactory requires 2 tokens, but", len(tokens), "were given.");
			return(False);

		if not self.bal_weights_equal_one(pool_data):
			return(False);

		int_with_decimals_weights = [int(Decimal(pool_data["tokens"][t]["weight"]) * Decimal(1e18)) for t in tokens];
		swap_fee_percentage = int(Decimal(pool_data["swapFeePercent"]) * Decimal(1e16));

		owner = self.bal_set_owner(pool_data);

		oracle_enabled = False;
		if "oracle_enabled" in pool_data.keys():
			oracle_enabled = pool_data["oracle_enabled"];
			if isinstance(oracle_enabled, str):
				if oracle_enabled.lower() == "true":
					oracle_enabled = True;
				else:
					oracle_enabled = False;

		create_function = factory.functions.create(	pool_data["name"],
													pool_data["symbol"],
													checksum_tokens,
													int_with_decimals_weights,
													swap_fee_percentage,
													oracle_enabled,
													owner);
		return(create_function);

	def bal_create_fn_stable_pool_factory(self, pool_data):
		factory = self.bal_get_factory_contract("StablePoolFactory");
		(tokens, checksum_tokens) = self.bal_sort_tokens(list(pool_data["tokens"].keys()));
		swap_fee_percentage = int(Decimal(pool_data["swapFeePercent"]) * Decimal(1e16));

		owner = self.bal_set_owner(pool_data);

		create_function = factory.functions.create(	pool_data["name"],
													pool_data["symbol"],
													checksum_tokens,
													int(pool_data["amplificationParameter"]),
													swap_fee_percentage,
													owner);
		return(create_function);

	def bal_create_fn_lb_pool_factory(self, pool_data):
		factory = self.bal_get_factory_contract("LiquidityBootstrappingPoolFactory");
		(tokens, checksum_tokens) = self.bal_sort_tokens(list(pool_data["tokens"].keys()));

		if not self.bal_weights_equal_one(pool_data):
			return(False);

		swap_fee_percentage = int(Decimal(pool_data["swapFeePercent"]) * Decimal(1e16));
		int_with_decimals_weights = [int(Decimal(pool_data["tokens"][t]["weight"]) * Decimal(1e18)) for t in tokens];
		owner = self.bal_set_owner(pool_data);

		if not owner == self.address:
			self.WARN("!!! You are not the owner for your LBP !!!")
			self.WARN("You:\t\t" + self.address)
			self.WARN("Pool Owner:\t" + owner)

			print();
			self.WARN("Only the pool owner can add liquidity. If you do not control " + owner + " then you will not be able to add liquidity!")
			self.WARN("If you DO control " + owner + ", you will need to use the \"INIT\" join type from that address")
			cancel_time_sec = 30;
			self.WARN("If the owner mismatch is was unintentional, you have " + str(cancel_time_sec) + " seconds to cancel with Ctrl+C.")
			time.sleep(cancel_time_sec);

		create_function = factory.functions.create(	pool_data["name"],
													pool_data["symbol"],
													checksum_tokens,
													int_with_decimals_weights,
													swap_fee_percentage,
													owner,
													pool_data["swapEnabledOnStart"]);
		return(create_function);

	def bal_create_fn_meta_stable_pool_factory(self, pool_data):
		factory = self.bal_get_factory_contract("MetaStablePoolFactory");
		(tokens, checksum_tokens) = self.bal_sort_tokens(list(pool_data["tokens"].keys()));
		swap_fee_percentage = int(Decimal(pool_data["swapFeePercent"]) * Decimal(1e16));
		owner = self.bal_set_owner(pool_data);

		rate_providers = [self.web3.toChecksumAddress(pool_data["tokens"][token]["rateProvider"]) for token in tokens]
		price_rate_cache_durations = [int(pool_data["tokens"][token]["priceRateCacheDuration"]) for token in tokens]

		create_function = factory.functions.create(	pool_data["name"],
													pool_data["symbol"],
													checksum_tokens,
													int(pool_data["amplificationParameter"]),
													rate_providers,
													price_rate_cache_durations,
													swap_fee_percentage,
													pool_data["oracleEnabled"],
													owner);
		return(create_function);

	def bal_create_fn_investment_pool_factory(self, pool_data):
		factory = self.bal_get_factory_contract("InvestmentPoolFactory");
		(tokens, checksum_tokens) = self.bal_sort_tokens(list(pool_data["tokens"].keys()));
		swap_fee_percentage = int(Decimal(pool_data["swapFeePercent"]) * Decimal(1e16));
		int_with_decimals_weights = [int(Decimal(pool_data["tokens"][t]["weight"]) * Decimal(1e18)) for t in tokens];
		management_fee_percentage = int(Decimal(pool_data["managementFeePercent"]) * Decimal(1e16));
		# Deployed factory doesn't allow asset managers
		# assetManagers = [0 for i in range(0,len(tokens))]
		owner = self.bal_set_owner(pool_data);
		if not owner == self.address:
			self.WARN("!!! You are not the owner for your Investment Pool !!!")
			self.WARN("You:\t\t" + self.address)
			self.WARN("Pool Owner:\t" + owner)

			print();
			self.WARN("Only the pool owner can call permissioned functions, such as changing weights or the management fee.")
			self.WARN(owner + " should either be you, or a multi-sig or other contract that you control and can call permissioned functions from.")
			cancel_time_sec = 30;
			self.WARN("If the owner mismatch is was unintentional, you have " + str(cancel_time_sec) + " seconds to cancel with Ctrl+C.")
			time.sleep(cancel_time_sec);

		create_function = factory.functions.create(	pool_data["name"],
													pool_data["symbol"],
													checksum_tokens,
													int_with_decimals_weights,
													swap_fee_percentage,
													owner,
													pool_data["swapEnabledOnStart"],
													management_fee_percentage);
		return(create_function);

	def bal_create_fn_stable_phantom_pool_factory(self, pool_data):
		factory = self.bal_get_factory_contract("StablePhantomPoolFactory");
		(tokens, checksum_tokens) = self.bal_sort_tokens(list(pool_data["tokens"].keys()));
		swap_fee_percentage = int(Decimal(pool_data["swapFeePercent"]) * Decimal(1e16));
		owner = self.bal_set_owner(pool_data);

		rate_providers = [self.web3.toChecksumAddress(pool_data["tokens"][token]["rateProvider"]) for token in tokens]
		token_rate_cache_durations = [int(pool_data["tokens"][token]["tokenRateCacheDuration"]) for token in tokens]

		print(pool_data["name"])
		print(pool_data["symbol"])
		print(checksum_tokens)
		print(int(pool_data["amplificationParameter"]))
		print(rate_providers)
		print(token_rate_cache_durations)
		print(swap_fee_percentage)
		print(owner)

		create_function = factory.functions.create(	pool_data["name"],
													pool_data["symbol"],
													checksum_tokens,
													int(pool_data["amplificationParameter"]),
													rate_providers,
													token_rate_cache_durations,
													swap_fee_percentage,
													owner);
		return(create_function);

	def bal_create_fn_linear_pool_factory(self, pool_data):
		factory = self.bal_get_factory_contract("LinearPoolFactory");
		(tokens, checksum_tokens) = self.bal_sort_tokens(list(pool_data["tokens"].keys()));
		swap_fee_percentage = int(Decimal(pool_data["swapFeePercent"]) * Decimal(1e16));
		owner = self.bal_set_owner(pool_data);

		main_token = None;
		wrapped_token = None;
		for token in pool_data["tokens"].keys():
			fields = pool_data["tokens"][token].keys();
			if "rate_provider" in fields and "token_rate_cache_duration" in fields:
				wrapped_token = token;
			else:
				main_token = token;
		if main_token == wrapped_token:
			self.ERROR("Must have one wrapped and one main token!");
			return(False);

		lower_target = int(pool_data["lower_target"]);
		upper_target = int(pool_data["upper_target"]);
		rate_provider = self.web3.toChecksumAddress(pool_data["tokens"][wrapped_token]["rate_provider"]);
		token_rate_cache_duration = int(pool_data["tokens"][wrapped_token]["token_rate_cache_duration"]);

		create_function = factory.functions.create(	pool_data["name"],
													pool_data["symbol"],
													self.web3.toChecksumAddress(main_token),
													self.web3.toChecksumAddress(wrapped_token),
													lower_target,
													upper_target,
													swap_fee_percentage,
													rate_provider,
													token_rate_cache_duration,
													owner);
		return(create_function);

	def bal_create_pool_in_factory(self, pool_description, gas_factor, gas_price_speed, nonce_override=-1, gas_estimate_override=-1, gas_price_gwei_override=-1):
		create_function = None;
		pool_factory_name = pool_description["poolType"] + "Factory";

		# list of all supported pool factories
		# NOTE: when you add a pool factory to this list, be sure to
		# 		add it to the printout of supported factories below
		if pool_factory_name == "WeightedPoolFactory":
			create_function = self.bal_create_fn_weighted_pool_factory(pool_description);
		if pool_factory_name == "WeightedPool2TokensFactory":
			create_function = self.bal_create_fn_weighted_pool2_tokens_factory(pool_description);
		if pool_factory_name == "StablePoolFactory":
			create_function = self.bal_create_fn_stable_pool_factory(pool_description);
		if pool_factory_name == "LiquidityBootstrappingPoolFactory":
			create_function = self.bal_create_fn_lb_pool_factory(pool_description);
		if pool_factory_name == "MetaStablePoolFactory":
			create_function = self.bal_create_fn_meta_stable_pool_factory(pool_description);
		if pool_factory_name == "InvestmentPoolFactory":
			create_function = self.bal_create_fn_investment_pool_factory(pool_description);
		if pool_factory_name == "StablePhantomPoolFactory":
			create_function = self.bal_create_fn_stable_phantom_pool_factory(pool_description);
		if pool_factory_name == "LinearPoolFactory":
			create_function = self.bal_create_fn_linear_pool_factory(pool_description);
		if create_function is None:
			print("No pool factory found with name:", pool_factory_name);
			print("Currently supported pool types are:");
			print("\tWeightedPool");
			print("\tWeightedPool2Token");
			print("\tStablePool");
			print("\tLiquidityBootstrappingPool");
			print("\tMetaStablePool");
			print("\tInvestmentPool");
			print("\tStablePhantomPool");
			print("\tLinearPool");
			return(False);

		if not create_function:
			self.ERROR("Pool creation failed.")
			return(False)
		print("Pool function created, generating transaction...");
		tx = self.build_tx(create_function, gas_factor, gas_price_speed, nonce_override, gas_estimate_override, gas_price_gwei_override);
		print("Transaction Generated!");
		tx_hash = self.send_tx(tx);
		return(tx_hash);

	def bal_get_pool_id_from_hash(self, tx_hash):
		receipt = self.get_tx_receipt(tx_hash, delay=2, max_retries=5);
		
		# PoolRegistered event lives in the Vault
		vault = self.web3.eth.contract(address=self.deployment_addresses["Vault"], abi=self.abis["Vault"]);
		logs = vault.events.PoolRegistered().processReceipt(receipt);
		pool_id = logs[0]['args']['pool_id'].hex();
		self.GOOD("\nDon't worry about that ^ warning, everything's fine :)");
		print("Your pool ID is:");
		print("\t0x" + str(pool_id));
		return(pool_id);

	def bal_join_pool_exact_in(self, join_description, gas_factor=1.05, gas_price_speed="average", nonce_override=-1, gas_estimate_override=-1, gas_price_gwei_override=-1):
		(sorted_tokens, checksum_tokens) = self.bal_sort_tokens(list(join_description["tokens"].keys()));
		amounts_by_sorted_tokens = [join_description["tokens"][token]["amount"] for token in sorted_tokens];
		raw_amounts = self.bal_convert_tokens_to_wei(sorted_tokens, amounts_by_sorted_tokens);

		user_data_encoded = eth_abi.encode_abi(	['uint256', 'uint256[]'],
												[self.join_kind["EXACT_TOKENS_IN_FOR_BPT_OUT"], raw_amounts]);
		join_pool_request_tuple = (checksum_tokens, raw_amounts, user_data_encoded.hex(), join_description["fromInternalBalance"]);
		vault = self.web3.eth.contract(address=self.deployment_addresses["Vault"], abi=self.abis["Vault"]);
		join_pool_function = vault.functions.joinPool(join_description["poolId"],
												self.web3.toChecksumAddress(self.web3.eth.default_account),
												self.web3.toChecksumAddress(self.web3.eth.default_account),
												join_pool_request_tuple);
		tx = self.build_tx(join_pool_function, gas_factor, gas_price_speed, nonce_override, gas_estimate_override, gas_price_gwei_override);
		print("Transaction Generated!");
		tx_hash = self.send_tx(tx);
		return(tx_hash);

	def bal_join_pool_token_in_for_exact_bpt_out(self, join_description, gas_factor=1.05, gas_price_speed="average", nonce_override=-1, gas_estimate_override=-1, gas_price_gwei_override=-1):
		(sorted_tokens, checksum_tokens) = self.bal_sort_tokens(list(join_description["tokens"].keys()));
		amounts_by_sorted_tokens = [join_description["tokens"][token]["amount"] for token in sorted_tokens];
		raw_amounts = self.bal_convert_tokens_to_wei(sorted_tokens, amounts_by_sorted_tokens);

		index = -1;
		counter = -1;
		for amt in raw_amounts:
			counter += 1;
			if amt > 0:
				if index == -1:
					index = counter;
				else:
					self.ERROR("Multiple tokens have amounts for a single token join! Only one token can have a non-zero amount!");
					return(False);
		if index == -1:
			self.ERROR("No tokens have amounts. You must have one token with a non-zero amount!");
			return(False);

		user_data_encoded = eth_abi.encode_abi(	['uint256', 'uint256', 'uint256'],
												[self.join_kind["TOKEN_IN_FOR_EXACT_BPT_OUT"], join_description["minBptOut"], index]);

		join_pool_request_tuple = (checksum_tokens, raw_amounts, user_data_encoded.hex(), join_description["fromInternalBalance"]);
		vault = self.web3.eth.contract(address=self.deployment_addresses["Vault"], abi=self.abis["Vault"]);
		join_pool_function = vault.functions.joinPool(join_description["poolId"],
												self.web3.toChecksumAddress(self.web3.eth.default_account),
												self.web3.toChecksumAddress(self.web3.eth.default_account),
												join_pool_request_tuple);
		tx = self.build_tx(join_pool_function, gas_factor, gas_price_speed, nonce_override, gas_estimate_override, gas_price_gwei_override);
		print("Transaction Generated!");
		tx_hash = self.send_tx(tx);
		return(tx_hash);

	def bal_register_pool_with_vault(self, pool_description, pool_id, gas_factor=1.05, gas_price_speed="average", nonce_override=-1, gas_estimate_override=-1, gas_price_gwei_override=-1):
		self.WARN("\"balRegisterPoolWithVault\" is deprecated. Please use \"balJoinPoolInit\".")
		self.bal_join_pool_init(pool_description, pool_id, gas_factor, gas_price_speed, nonce_override, gas_estimate_override, gas_price_gwei_override)

	def bal_join_pool_init(self, pool_description, pool_id, gas_factor=1.05, gas_price_speed="average", nonce_override=-1, gas_estimate_override=-1, gas_price_gwei_override=-1):

		(sorted_tokens, checksum_tokens) = self.bal_sort_tokens(list(pool_description["tokens"].keys()));
		initial_balances_by_sorted_tokens = [pool_description["tokens"][token]["initialBalance"] for token in sorted_tokens];

		raw_init_balances = self.bal_convert_tokens_to_wei(sorted_tokens, initial_balances_by_sorted_tokens);
		init_user_data_encoded = eth_abi.encode_abi(	['uint256', 'uint256[]'], 
													[self.join_kind["INIT"], raw_init_balances]);

		#todo replace this code with a join call
		join_pool_request_tuple = (checksum_tokens, raw_init_balances, init_user_data_encoded.hex(), pool_description["fromInternalBalance"]);
		vault = self.web3.eth.contract(address=self.deployment_addresses["Vault"], abi=self.abis["Vault"]);
		join_pool_function = vault.functions.joinPool(pool_id, 
												self.web3.toChecksumAddress(self.web3.eth.default_account), 
												self.web3.toChecksumAddress(self.web3.eth.default_account), 
												join_pool_request_tuple);
		tx = self.build_tx(join_pool_function, gas_factor, gas_price_speed, nonce_override, gas_estimate_override, gas_price_gwei_override);
		print("Transaction Generated!");		
		tx_hash = self.send_tx(tx);
		return(tx_hash);

	def bal_vault_weth(self):
		vault = self.web3.eth.contract(address=self.deployment_addresses["Vault"], abi=self.abis["Vault"]);
		weth_address = vault.functions.WETH().call();
		return(weth_address);

	def bal_vault_get_pool_tokens(self, pool_id):
		vault = self.web3.eth.contract(address=self.deployment_addresses["Vault"], abi=self.abis["Vault"]);
		output = vault.functions.getPoolTokens(pool_id).call();
		tokens = output[0];
		balances = output[1];
		last_change_block = output[2];
		return (tokens, balances, last_change_block);

	def bal_vault_get_internal_balance(self, tokens, address=None):
		if address is None:
			address = self.web3.eth.default_account;

		vault = self.web3.eth.contract(address=self.deployment_addresses["Vault"], abi=self.abis["Vault"]);
		(sorted_tokens, checksum_tokens) = self.bal_sort_tokens(tokens);
		balances = vault.functions.getInternalBalance(address, checksum_tokens).call();
		num_elements = len(sorted_tokens);
		internal_balances = {};
		for i in range(num_elements):
			token = checksum_tokens[i];
			decimals = self.erc20_get_decimals(token);
			internal_balances[token] = Decimal(balances[i]) * Decimal(10**(-decimals));
		return(internal_balances);

	def bal_vault_do_manage_user_balance(self, kind, token, amount, sender, recipient, is_async=False, gas_factor=1.05, gas_price_speed="average", nonce_override=-1, gas_estimate_override=-1, gas_price_gwei_override=-1):
		if self.verbose:
			print("Managing User Balance");
			print("\tKind:\t\t", self.inverse_user_balance_op_kind[kind]);
			print("\tToken:\t\t", str(token));
			print("\tAmount:\t\t", str(amount));
			print("\tSender:\t\t", str(sender));
			print("\tRecipient:\t", str(recipient));
		manage_user_balance_fn = self.bal_vault_build_manage_user_balance_fn(kind, token, amount, sender, recipient);

		print();
		print("Building ManageUserBalance");
		tx = self.build_tx(manage_user_balance_fn, gas_factor, gas_price_speed, nonce_override, gas_estimate_override, gas_price_gwei_override);
		tx_hash = self.send_tx(tx, is_async);
		return(tx_hash);

	def bal_vault_build_manage_user_balance_fn(self, kind, token, amount, sender, recipient):
		kind = kind;
		asset = self.web3.toChecksumAddress(token);
		amount = self.bal_convert_tokens_to_wei([token],[amount])[0];
		sender = self.web3.toChecksumAddress(sender);
		recipient = self.web3.toChecksumAddress(recipient);
		input_tuple_list = [(kind, asset, amount, sender, recipient)];

		vault = self.web3.eth.contract(address=self.deployment_addresses["Vault"], abi=self.abis["Vault"]);
		manage_user_balance_fn = vault.functions.manageUserBalance(input_tuple_list);
		return(manage_user_balance_fn);

	def bal_pool_get_abi(self, pool_type):
		abi_path = os.path.join('abi/pools/'+ pool_type + '.json');
		f = pkgutil.get_data(__name__, abi_path).decode();
		pool_abi = json.loads(f);
		return(pool_abi);

	def bal_poold_id_to_address(self, pool_id):
		pool_address = self.web3.toChecksumAddress(pool_id[:42]);
		return(pool_address);

	def bal_get_pool_creation_data(self, pool_id, verbose=False, input_hash=None):
		address = self.bal_poold_id_to_address(pool_id);
		if input_hash is None:
			txns = self.get_transactions_by_address(address, internal=True, verbose=verbose);
		else:
			txns = self.get_transaction_by_hash(input_hash, verbose=verbose);

		pool_type_by_contract = {};
		for pool_type in self.deployment_addresses.keys():
			deployment_address = self.deployment_addresses[pool_type].lower();
			pool_type_by_contract[deployment_address] = pool_type;

		pool_factory_type = None;
		if input_hash is None:
			for txn in txns:
				if txn["from"].lower() in pool_type_by_contract.keys():
					pool_factory_type = pool_type_by_contract[txn["from"].lower()];
					tx_hash = txn["hash"];
					stamp = txn["timeStamp"];
					break;
		else:
			txn = txns["result"];
			if verbose:
				print();
				print(txn);
			pool_factory_type = pool_type_by_contract[txn["to"].lower()];
			tx_hash = txn["hash"];
			stamp = self.web3.eth.get_block(int(txn["blockNumber"],16))["timestamp"];

		return(address, pool_factory_type, tx_hash, stamp);

	def bal_get_pool_factory_creation_time(self, address):
		txns = self.get_transactions_by_address(address);
		return(txns[0]["timeStamp"]);

	def get_input_data(self, tx_hash):
		transaction = self.web3.eth.get_transaction(tx_hash);
		return(transaction.input)

	def bal_generate_pool_creation_arguments(self, pool_id, verbose=False, creation_hash=None):
		if self.network in ["polygon"] and creation_hash is None:
			self.ERROR("Verifying on polygon requires you to pass creation_hash")
			return(False)
		if self.network in ["arbitrum"]:
			self.ERROR("Automated pool verification doesn't work on " + self.network + " yet. Please try the method outlined in the docs using Tenderly.");
			return(False);

		# query etherscan for internal transactions to find pool factory, pool creation time, and creation hash
		(address, pool_factory_type, tx_hash, stamp_pool) = self.bal_get_pool_creation_data(pool_id, verbose=verbose, input_hash=creation_hash);

		# get the input data used to generate the pool
		input_data = self.get_input_data(tx_hash);

		# decode those ^ inputs according to the relevant pool factory ABI
		pool_factory_address = self.deployment_addresses[pool_factory_type];
		pool_factory_abi = self.abis[pool_factory_type];
		pool_factory_contract = self.web3.eth.contract(address=pool_factory_address, abi=pool_factory_abi);
		decoded_pool_data = pool_factory_contract.decode_function_input(input_data)[1];

		# get pool factory creation time to calculate pauseWindowDuration
		stamp_factory = self.bal_get_pool_factory_creation_time(pool_factory_address);

		# make sure arguments exist/are proper types to be encoded
		if "weights" in decoded_pool_data.keys():
			for i in range(len(decoded_pool_data["weights"])):
				decoded_pool_data["weights"][i] = int(decoded_pool_data["weights"][i]);
		if "priceRateCacheDuration" in decoded_pool_data.keys():
			for i in range(len(decoded_pool_data["priceRateCacheDuration"])):
				decoded_pool_data["priceRateCacheDuration"][i] = int(decoded_pool_data["priceRateCacheDuration"][i]);
		if pool_factory_type == "InvestmentPoolFactory" and not "assetManagers" in decoded_pool_data.keys():
			decoded_pool_data["assetManagers"] = [];
			for i in range(len(decoded_pool_data["weights"])):
				decoded_pool_data["assetManagers"].append(self.ZERO_ADDRESS);

		# times for pause/buffer
		days_to_sec = 24*60*60; # hr * min * sec
		pause_days = 90;
		buffer_period_days = 30;

		# calculate proper durations
		pause_window_duration_sec = max( (pause_days*days_to_sec) - (int(stamp_pool) - int(stamp_factory)), 0);
		buffer_period_duration_sec = buffer_period_days * days_to_sec;
		if pause_window_duration_sec == 0:
			buffer_period_duration_sec = 0;

		pool_type = pool_factory_type.replace("Factory","");
		pool_abi = self.bal_pool_get_abi(pool_type);

		struct_in_constructor = False;
		if pool_type == "WeightedPool":
			args = [self.deployment_addresses["Vault"],
					decoded_pool_data["name"],
					decoded_pool_data["symbol"],
					decoded_pool_data["tokens"],
					decoded_pool_data["weights"],
					int(decoded_pool_data["swapFeePercentage"]),
					int(pause_window_duration_sec),
					int(buffer_period_duration_sec),
					decoded_pool_data["owner"]];
		elif pool_type == "WeightedPool2Tokens":
			args = [self.deployment_addresses["Vault"],
					decoded_pool_data["name"],
					decoded_pool_data["symbol"],
					decoded_pool_data["tokens"][0],
					decoded_pool_data["tokens"][1],
					int(decoded_pool_data["weights"][0]),
					int(decoded_pool_data["weights"][1]),
					int(decoded_pool_data["swapFeePercentage"]),
					int(pause_window_duration_sec),
					int(buffer_period_duration_sec),
					decoded_pool_data["oracleEnabled"],
					decoded_pool_data["owner"]];
			struct_in_constructor = True;
		elif pool_type == "StablePool":
			args = [self.deployment_addresses["Vault"],
					decoded_pool_data["name"],
					decoded_pool_data["symbol"],
					decoded_pool_data["tokens"],
					int(decoded_pool_data["amplificationParameter"]),
					int(decoded_pool_data["swapFeePercentage"]),
					int(pause_window_duration_sec),
					int(buffer_period_duration_sec),
					decoded_pool_data["owner"]];
		elif pool_type == "MetaStablePool":
			args = [self.deployment_addresses["Vault"],
					decoded_pool_data["name"],
					decoded_pool_data["symbol"],
					decoded_pool_data["tokens"],
					decoded_pool_data["rateProviders"],
					decoded_pool_data["priceRateCacheDuration"],
					int(decoded_pool_data["amplificationParameter"]),
					int(decoded_pool_data["swapFeePercentage"]),
					int(pause_window_duration_sec),
					int(buffer_period_duration_sec),
					decoded_pool_data["oracleEnabled"],
					decoded_pool_data["owner"]];
			struct_in_constructor = True;
		elif pool_type == "LiquidityBootstrappingPool":
			args = [self.deployment_addresses["Vault"],
					decoded_pool_data["name"],
					decoded_pool_data["symbol"],
					decoded_pool_data["tokens"],
					decoded_pool_data["weights"],
					int(decoded_pool_data["swapFeePercentage"]),
					int(pause_window_duration_sec),
					int(buffer_period_duration_sec),
					decoded_pool_data["owner"],
					decoded_pool_data["swapEnabledOnStart"]];
		elif pool_type == "InvestmentPool":
			args = [self.deployment_addresses["Vault"],
					decoded_pool_data["name"],
					decoded_pool_data["symbol"],
					decoded_pool_data["tokens"],
					decoded_pool_data["weights"],
					decoded_pool_data["assetManagers"],
					int(decoded_pool_data["swapFeePercentage"]),
					int(pause_window_duration_sec),
					int(buffer_period_duration_sec),
					decoded_pool_data["owner"],
					decoded_pool_data["swapEnabledOnStart"],
					int(decoded_pool_data["managementSwapFeePercentage"])];
			struct_in_constructor = True;
		else:
			self.ERROR("PoolType", pool_type, "not found!")
			return(False);

		# encode constructor data
		pool_contract = self.web3.eth.contract(address=address, abi=pool_abi);
		if struct_in_constructor:
			args = (tuple(args),)
		data = pool_contract._encode_constructor_data(args=args);
		encoded_data = data[2:]; #cut off the 0x

		command = "yarn hardhat verify-contract --id {} --name {} --address {} --network {} --key {} --args {}"
		output = command.format(self.contract_directories[pool_factory_type]["directory"],
								pool_type,
								address,
								self.network,
								self.etherscan_api_key,
								encoded_data)
		return(output);

	def bal_stable_pool_get_amplification_parameter(self, pool_id):
		pool_address = self.web3.toChecksumAddress(pool_id[:42]);
		pool = self.web3.eth.contract(address=pool_address, abi=self.bal_pool_get_abi("StablePool"));
		(value, is_updating, precision) = pool.functions.getAmplificationParameter().call();
		return(value, is_updating, precision); 
	
	def bal_stable_pool_start_amplification_parameter_update(self, pool_id, raw_end_value, end_time, is_async=False, gas_factor=1.05, gas_price_speed="average", nonce_override=-1, gas_estimate_override=-1, gas_price_gwei_override=-1):
		pool_address = self.web3.toChecksumAddress(pool_id[:42]);
		pool = self.web3.eth.contract(address=pool_address, abi=self.bal_pool_get_abi("StablePool"));
		 
		owner = pool.functions.getOwner().call();
		if not self.address == owner:
			self.ERROR("You are not the pool owner; this transaction will fail.");
			return(False);

		fn = pool.functions.startAmplificationParameterUpdate(raw_end_value, end_time);
		tx = self.build_tx(fn, gas_factor, gas_price_speed, nonce_override, gas_estimate_override, gas_price_gwei_override);
		tx_hash = self.send_tx(tx, is_async);
		return(tx_hash);

	# https://dev.balancer.fi/references/contracts/apis/pools/weightedpool2tokens#gettimeweightedaverage
	def bal_oracle_pool_get_time_weighted_average(self, pool_id, queries):
		pool_address = self.web3.toChecksumAddress(pool_id[:42]);
		pool = self.web3.eth.contract(address=pool_address, abi=self.bal_pool_get_abi("WeightedPool2Tokens"));
		results = pool.functions.getTimeWeightedAverage(queries).call();
		return(results);

	def bal_swap_is_flash_swap(self, swap_description):
		for amount in swap_description["limits"]:
			if not float(amount) == 0.0:
				return(False);
		return(True);

	def bal_reorder_token_dicts(self, tokens):
		original_idx_to_sorted_idx = {};
		sorted_idx_to_original_idx = {};
		token_address_to_idx = {};
		for i in range(len(tokens)):
			token_address_to_idx[tokens[i]] = i;
		sorted_tokens = tokens;
		sorted_tokens.sort();
		for i in range(len(sorted_tokens)):
			original_idx_to_sorted_idx[token_address_to_idx[sorted_tokens[i]]] = i;
			sorted_idx_to_original_idx[i] = token_address_to_idx[sorted_tokens[i]];
		return(sorted_tokens, original_idx_to_sorted_idx, sorted_idx_to_original_idx);

	def bal_swap_get_user_data(self, pool_type):
		user_data_null = eth_abi.encode_abi(['uint256'], [0]);
		user_data = user_data_null;
		#for weightedPools, user data is just null, but in the future there may be user_data to pass to pools for swaps
		# if pool_type == "someFuturePool":
		# 	user_data = "something else";
		return(user_data);

	def bal_do_swap(self, swap_description, is_async=False, gas_factor=1.05, gas_price_speed="average", nonce_override=-1, gas_estimate_override=-1, gas_price_gwei_override=-1):
		swap_fn = self.bal_create_fn_swap(swap_description);
		tx = self.build_tx(swap_fn, gas_factor, gas_price_speed, nonce_override, gas_estimate_override, gas_price_gwei_override);
		tx_hash = self.send_tx(tx, is_async);
		return(tx_hash);

	def bal_do_batch_swap(self, swap_description, is_async=False, gas_factor=1.05, gas_price_speed="average", nonce_override=-1, gas_estimate_override=-1, gas_price_gwei_override=-1):
		batch_swap_fn = self.bal_create_fn_batch_swap(swap_description);
		tx = self.build_tx(batch_swap_fn, gas_factor, gas_price_speed, nonce_override, gas_estimate_override, gas_price_gwei_override);
		tx_hash = self.send_tx(tx, is_async);
		return(tx_hash);

	def bal_create_fn_swap(self, swap_description):
		kind = int(swap_description["kind"])
		limited_token = None;
		amount_token = None;
		if kind == 0: #GIVEN_IN
			amount_token = swap_description["assetIn"];
			limited_token = swap_description["assetOut"];
		elif kind == 1: #GIVEN_OUT
			amount_token = swap_description["assetOut"];
			limited_token = swap_description["assetIn"];

		amount_wei = int(Decimal(swap_description["amount"]) * 10 ** Decimal(self.erc20_get_decimals(amount_token)));
		limit_wei = int(Decimal(swap_description["limit"]) * 10 ** Decimal(self.erc20_get_decimals(limited_token)));

		swap_struct = (
			swap_description["poolId"],
			kind,
			self.web3.toChecksumAddress(swap_description["assetIn"]),
			self.web3.toChecksumAddress(swap_description["assetOut"]),
			amount_wei,
			self.bal_swap_get_user_data(None)
		)
		fund_struct = (
			self.web3.toChecksumAddress(swap_description["fund"]["sender"]),
			swap_description["fund"]["fromInternalBalance"],
			self.web3.toChecksumAddress(swap_description["fund"]["recipient"]),
			swap_description["fund"]["toInternalBalance"]
		)
		vault = self.web3.eth.contract(address=self.deployment_addresses["Vault"], abi=self.abis["Vault"]);
		single_swap_function = vault.functions.swap(
			swap_struct,
			fund_struct,
			limit_wei,
			int(swap_description["deadline"])
		)
		return(single_swap_function);

	def bal_create_fn_batch_swap(self, swap_description):
		(sorted_tokens, original_idx_to_sorted_idx, sorted_idx_to_original_idx) = self.bal_reorder_token_dicts(swap_description["assets"]);
		num_tokens = len(sorted_tokens);

		# reorder the limits to refer to properly sorted tokens
		reordered_limits = [];
		for i in range(num_tokens):
			curr_limit_standard = float(swap_description["limits"][sorted_idx_to_original_idx[i]]);
			decimals = self.erc20_get_decimals(sorted_tokens[i]);
			curr_limit_raw = int(Decimal(curr_limit_standard) * Decimal(10**(decimals)))
			reordered_limits.append(curr_limit_raw)

		kind = int(swap_description["kind"]);
		assets = [self.web3.toChecksumAddress(token) for token in sorted_tokens];

		swaps_tuples = [];
		for swap in swap_description["swaps"]:
			idx_sorted_in = original_idx_to_sorted_idx[int(swap["assetInIndex"])];
			idx_sorted_out = original_idx_to_sorted_idx[int(swap["assetOutIndex"])];
			decimals = self.erc20_get_decimals(sorted_tokens[idx_sorted_in]);
			amount = int( Decimal(swap["amount"]) * Decimal(10**(decimals)) );

			swaps_tuple = (	swap["poolId"],
							idx_sorted_in,
							idx_sorted_out,
							amount,
							self.bal_swap_get_user_data(None));
			swaps_tuples.append(swaps_tuple);

		funds = (	self.web3.toChecksumAddress(swap_description["funds"]["sender"]),
					swap_description["funds"]["fromInternalBalance"],
					self.web3.toChecksumAddress(swap_description["funds"]["recipient"]),
					swap_description["funds"]["toInternalBalance"]);
		int_reordered_limits = [int(element) for element in reordered_limits];
		deadline = int(swap_description["deadline"]);
		vault = self.web3.eth.contract(address=self.deployment_addresses["Vault"], abi=self.abis["Vault"]);
		batch_swap_function = vault.functions.batchSwap(	kind,
														swaps_tuples,
														assets,
														funds,
														int_reordered_limits,
														deadline);
		return(batch_swap_function);

	def bal_get_link_to_frontend(self, pool_id):
		if "balFrontend" in self.network_params[self.network].keys():
			return("https://" + self.network_params[self.network]["balFrontend"] + "pool/0x" + pool_id);
		else:
			return("")

	def multi_call_load_contract(self):
		abi_path = os.path.join('abi/multi_call.json');
		f = pkgutil.get_data(__name__, abi_path).decode();
		abi = json.loads(f);
		if self.network == "arbitrum":
			multicall_address = "0x269ff446d9892c9e19082564df3f5e8741e190a1";
		else:
			multicall_address = MULTICALL_ADDRESSES[self.network_params[self.network]["id"]];
		multi_call = self.web3.eth.contract(self.web3.toChecksumAddress(multicall_address), abi=abi);
		return(multi_call);

	def multi_call_erc20_batch_decimals(self, tokens):
		multi_call = self.multi_call_load_contract();

		payload = [];
		for token in tokens:
			curr_token_contract = self.erc20_get_contract(token);
			call_data = curr_token_contract.encodeABI(fn_name='decimals');
			chk_token = self.web3.toChecksumAddress(token);
			payload.append((chk_token, call_data));

		# make the actual call to MultiCall
		output_data = multi_call.functions.aggregate(payload).call();
		tokens_to_decimals = {};

		fn = curr_token_contract.get_function_by_name(fn_name='decimals');
		output_abi = get_abi_output_types(fn.abi);

		for token, odBytes in zip(tokens, output_data[1]):
			decoded_output_data = self.web3.codec.decode_abi(output_abi, odBytes);
			decimals = decoded_output_data[0];
			tokens_to_decimals[token] = decimals;
			self.decimals[token] = decimals;

		return(tokens_to_decimals);

	# multiprocessing helper
	def chunks(self, a, n):
		k, m = divmod(len(a), n)
		return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

	def get_onchain_data(self, pools, procs=None):
		# load the multicall contract
		multi_call = self.multi_call_load_contract();

		# load the vault contract
		vault = self.web3.eth.contract(address=self.deployment_addresses["Vault"], abi=self.abis["Vault"]);
		target = self.deployment_addresses["Vault"];

		pool_abis = {};
		for pool_type in pools.keys():
			abi_path = os.path.join('abi/pools/'+pool_type+'Pool.json');
			f = pkgutil.get_data(__name__, abi_path).decode();
			pool_abi = json.loads(f);
			pool_abis[pool_type] = pool_abi;

		payload = [];
		pid_and_fns = [];
		output_abis = {};

		pool_to_type = {};
		for pool_type in pools.keys():
			pool_ids = pools[pool_type];
			pool_abi = pool_abis[pool_type];
			# construct all the calls in format (VaultAddress, encodedCallData)
			for pool_id in pool_ids:
				pool_to_type[pool_id] = pool_type;
				pool_address = self.web3.toChecksumAddress(pool_id[:42]);
				curr_pool = self.web3.eth.contract(address=pool_address, abi=pool_abi);

				# === all pools need tokens and swap fee ===
				# get pool tokens
				call_data = vault.encodeABI(fn_name='getPoolTokens', args=[pool_id]);
				payload.append((target, call_data));
				pid_and_fns.append((pool_id, 'getPoolTokens'));
				if not 'getPoolTokens' in output_abis.keys():
					fn = vault.get_function_by_name(fn_name='getPoolTokens');
					output_abis['getPoolTokens'] = get_abi_output_types(fn.abi);
				# get swap fee
				call_data = curr_pool.encodeABI(fn_name='getSwapFeePercentage');
				payload.append((pool_address, call_data));
				pid_and_fns.append((pool_id, 'getSwapFeePercentage'));
				if not 'getSwapFeePercentage' in output_abis.keys():
					fn = curr_pool.get_function_by_name(fn_name='getSwapFeePercentage');
					output_abis['getSwapFeePercentage'] = get_abi_output_types(fn.abi);
				# get paused state
				call_data = curr_pool.encodeABI(fn_name='getPausedState');
				payload.append((pool_address, call_data));
				pid_and_fns.append((pool_id, 'getPausedState'));
				if not 'getPausedState' in output_abis.keys():
					fn = curr_pool.get_function_by_name(fn_name='getPausedState');
					output_abis['getPausedState'] = get_abi_output_types(fn.abi);

				# === using weighted math ===
				if pool_type in ["Weighted", "LiquidityBootstrapping", "Investment"]:
					call_data = curr_pool.encodeABI(fn_name='getNormalizedWeights');
					payload.append((pool_address, call_data));
					pid_and_fns.append((pool_id, 'getNormalizedWeights'));
					if not 'getNormalizedWeights' in output_abis.keys():
						fn = curr_pool.get_function_by_name(fn_name='getNormalizedWeights');
						output_abis['getNormalizedWeights'] = get_abi_output_types(fn.abi);

				# === using stable math ===
				if pool_type in ["Stable", "MetaStable"]:
					call_data = curr_pool.encodeABI(fn_name='getAmplificationParameter');
					payload.append((pool_address, call_data));
					pid_and_fns.append((pool_id, 'getAmplificationParameter'));
					if not 'getAmplificationParameter' in output_abis.keys():
						fn = curr_pool.get_function_by_name(fn_name='getAmplificationParameter');
						output_abis['getAmplificationParameter'] = get_abi_output_types(fn.abi);

				# === have pausable swaps by pool owner ===
				if pool_type in [ "LiquidityBootstrapping", "Investment"]:
					call_data = curr_pool.encodeABI(fn_name='getSwapEnabled');
					payload.append((pool_address, call_data));
					pid_and_fns.append((pool_id, 'getSwapEnabled'));
					if not 'getSwapEnabled' in output_abis.keys():
						fn = curr_pool.get_function_by_name(fn_name='getSwapEnabled');
						output_abis['getSwapEnabled'] = get_abi_output_types(fn.abi);

		# make the actual call to MultiCall
		output_data = multi_call.functions.aggregate(payload).call();

		chain_data_out = {};
		chain_data_bookkeeping = {};
		decoded_output_data_blocks = [];

		if procs is None:
			decoded_output_data_blocks = [self.web3.codec.decode_abi(output_abis[pidAndFn[1]], od_bytes) for od_bytes, pidAndFn in zip(output_data[1], pid_and_fns)]
		else:
			if procs == 0:
				procs = multiprocessing.cpu_count();

			zipped_data = list(zip(output_data[1], pid_and_fns));
			input_data_chunks = list(self.chunks(zipped_data, procs));

			manager = multiprocessing.Manager()
			return_dict = manager.dict()
			jobs = [];

			for i in range(0, procs):
				process = multiprocessing.Process(	target=process_data,
													args=(i, self.endpoint, input_data_chunks[i], output_abis, return_dict))
				jobs.append(process)
			# Start the processes
			for j in jobs:
				j.start()
			# Ensure all of the processes have finished
			for j in jobs:
				j.join()
			sorted_keys = list(return_dict.keys());
			sorted_keys.sort();
			for i in sorted_keys:
				decoded_output_data_blocks.extend(return_dict[i]);

		for decoded_output_data, odBytes, pidAndFn in zip(decoded_output_data_blocks,output_data[1], pid_and_fns):
			pool_id = pidAndFn[0];
			decoder = pidAndFn[1];
			if not pool_id in chain_data_out.keys():
				chain_data_out[pool_id] = {"pool_type":pool_to_type[pool_id]};
				chain_data_bookkeeping[pool_id] = {};

			if decoder == "getPoolTokens":
				addresses = list(decoded_output_data[0]);
				balances = 	list(decoded_output_data[1]);
				last_change_block = decoded_output_data[2];

				chain_data_out[pool_id]["last_change_block"] = last_change_block;
				chain_data_bookkeeping[pool_id]["orderedAddresses"] = addresses;

				chain_data_out[pool_id]["tokens"] = {};
				for address, balance in zip(addresses, balances):
					chain_data_out[pool_id]["tokens"][address] = {"raw_balance":str(balance)};

			elif decoder == "getNormalizedWeights":
				normalized_weights = list(decoded_output_data[0]);
				addresses = chain_data_bookkeeping[pool_id]["orderedAddresses"];
				for address, normalizedWeight in zip(addresses, normalized_weights):
					weight = Decimal(str(normalizedWeight)) * Decimal(str(1e-18));
					chain_data_out[pool_id]["tokens"][address]["weight"] = str(weight);

			elif decoder == "getSwapFeePercentage":
				swap_fee = Decimal(decoded_output_data[0]) * Decimal(str(1e-18));
				chain_data_out[pool_id]["swap_fee"] = str(swap_fee);

			elif decoder == "getAmplificationParameter":
				raw_amp  = Decimal(decoded_output_data[0]);
				scaling = Decimal(decoded_output_data[2]);
				chain_data_out[pool_id]["amp"] = str(raw_amp/scaling);

			elif decoder == "getSwapEnabled":
				chain_data_out[pool_id]["swapEnabled"] = decoded_output_data[0];

			elif decoder == "getPausedState":
				chain_data_out[pool_id]["pausedState"] = decoded_output_data[0];

		#find tokens for which decimals have not been cached
		tokens = set();
		for pool in chain_data_out.keys():
			for token in chain_data_out[pool]["tokens"].keys():
				tokens.add(token);
		have_decimals_for = set(self.decimals.keys());

		# set subtraction (A - B) gives "What is in A that isn't in B?"
		need_decimals_for = tokens - have_decimals_for;

		#if there are any, query them onchain using multicall
		if len(need_decimals_for) > 0:
			print("New tokens found. Caching decimals for", len(need_decimals_for), "tokens...")
			self.multi_call_erc20_batch_decimals(need_decimals_for);

		# update rawBalances to have decimal adjusted values
		for pool in chain_data_out.keys():
			for token in chain_data_out[pool]["tokens"].keys():
				raw_balance = chain_data_out[pool]["tokens"][token]["raw_balance"];
				decimals = self.erc20_get_decimals(token);
				chain_data_out[pool]["tokens"][token]["balance"] = str(Decimal(raw_balance) * Decimal(10**(-decimals)));

		return(chain_data_out);