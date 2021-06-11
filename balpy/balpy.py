# balpy.py

# python basics
import json
import os
import requests
import time
import sys
import pkgutil

# web3 
from web3 import Web3
import eth_abi

# globals
global web3
global lastEtherscanCallTime
global etherscanMaxRate
global etherscanApiKey

class balpy(object):
	
	"""
	Balancer Protocol Python API
	Interface with Balancer V2 Smart contracts directly from Python
	"""

	# Contract addresses -- same across mainnet and testnets
	VAULT =                  '0xBA12222222228d8Ba445958a75a0704d566BF2C8';
	WEIGHTED_POOL_FACTORY =  '0x8E9aa87E45e92bad84D5F8DD1bff34Fb92637dE9';
	DELEGATE_OWNER =         '0xBA1BA1ba1BA1bA1bA1Ba1BA1ba1BA1bA1ba1ba1B';
	ZERO_ADDRESS =           '0x0000000000000000000000000000000000000000';

	# Constants
	INFINITE = 2 ** 256 - 1; #for infinite unlock

	# Environment variable names
	envVarEtherscan = 	"KEY_API_ETHERSCAN";
	envVarInfura = 		"KEY_API_INFURA";
	envVarPrivate = 	"KEY_PRIVATE";
	
	# Etherscan API call management	
	lastEtherscanCallTime = 0;
	etherscanMaxRate = 5.0; #hz
	etherscanSpeedDict = {
			"slow":"SafeGasPrice",
			"average":"ProposeGasPrice",
			"fast":"FastGasPrice"
	};

	# Network parameters
	networkParams = {	"mainnet":	{"id":1,	"etherscanSubdomain":""},
						"kovan":	{"id":42,	"etherscanSubdomain":"kovan."}};

	# ABIs, Artifacts
	artifacts = ["Vault", "WeightedPoolFactory"];
	abis = {};
	contractAddresses = {"Vault":VAULT, "WeightedPoolFactory":WEIGHTED_POOL_FACTORY};
	
	decimals = {};
	erc20Contracts = {};

	def __init__(self, network=None, verbose=True):
		super(balpy, self).__init__();

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

		self.etherscanApiKey = 		os.environ.get(self.envVarEtherscan);
		self.infuraApiKey = 		os.environ.get(self.envVarInfura);
		self.privateKey =  			os.environ.get(self.envVarPrivate);
		if self.etherscanApiKey is None or self.infuraApiKey is None or self.privateKey is None:
			self.ERROR("You need to add your keys to the your environment variables");
			print("\t\texport " + self.envVarEtherscan + "=<yourEtherscanApiKey>");
			print("\t\texport " + self.envVarInfura + "=<yourInfuraApiKey>");
			print("\t\texport " + self.envVarPrivate + "=<yourPrivateKey>");
			quit();

		self.network = network;

		# TODO: add non-Infura HTTPProvider
		# connect to infura, set wallet
		endpoint = 'https://' + self.network + '.infura.io/v3/' + self.infuraApiKey;
		self.web3 = Web3(Web3.HTTPProvider(endpoint));
		acct = self.web3.eth.account.privateKeyToAccount(self.privateKey);
		self.web3.eth.default_account = acct.address;
		self.address = acct.address;

		if self.verbose:
			print("Initialized account", self.web3.eth.default_account);
			print("Connected to web3 at", endpoint);

		# Read files packaged in module
		for name in self.artifacts:
			artifactPath = os.path.join('artifacts/', self.network, name + '.json');
			f = pkgutil.get_data(__name__, artifactPath).decode();
			self.abis[name] = json.loads(f)["abi"];

	# ======================
	# ====Color Printing====
	# ======================
	def WARNING(self, text):
		WARNING_BEGIN = '\033[93m';
		WARNING_END = '\033[0m';
		print(WARNING_BEGIN + "[WARNING] " + text + WARNING_END);

	def ERROR(self, text):
		ERROR_BEGIN = '\033[91m';
		ERROR_END = '\033[0m';
		print(ERROR_BEGIN + "[ERROR] " + text + ERROR_END);

	# =====================
	# ===Transaction Fns===
	# =====================
	def buildTx(self, fn, gasFactor, gasSpeed="average", nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):
		chainIdNetwork = self.networkParams[self.network]["id"];

		# Get nonce if not overridden
		if nonceOverride > -1:
			nonce = nonceOverride;
		else:
			nonce = self.web3.eth.get_transaction_count(self.web3.eth.default_account)

		# Calculate gas estimate if not overridden
		if gasEstimateOverride > -1:
			gasEstimate = gasEstimateOverride;
		else:
			gasEstimate = int(fn.estimateGas() * gasFactor);

		# Get gas price from Etherscan if not overridden
		if gasPriceGweiOverride > -1:
			gasPriceGwei = gasPriceGweiOverride;
		else:
			if not chainIdNetwork == 1: #if not mainnet
				gasPriceGwei = 5;
				pass;
			gasPriceGwei = self.getGasPriceEtherscanGwei(gasSpeed);
		
		print("Gas Estimate:\t", gasEstimate);
		print("Gas Price:\t", gasPriceGwei, "Gwei");
		print("Nonce:\t\t", nonce);

		# build transaction
		data = fn.buildTransaction({'chainId': chainIdNetwork,
								    'gas': gasEstimate,
								    'gasPrice': self.web3.toWei(gasPriceGwei, 'gwei'),
								    'nonce': nonce,
									});
		return(data);

	def sendTx(self, tx, isAsync=False):
		signedTx = self.web3.eth.account.sign_transaction(tx, self.privateKey);
		txHash = self.web3.eth.send_raw_transaction(signedTx.rawTransaction).hex();

		print("Sending transaction, view progress at:");
		print("\thttps://"+self.networkParams[self.network]["etherscanSubdomain"]+"etherscan.io/tx/"+txHash);
		
		if not isAsync:
			self.waitForTx(txHash);
		return(txHash);

	def waitForTx(self, txHash, timeOutSec=120):
		print("Waiting for tx:", txHash);
		self.web3.eth.wait_for_transaction_receipt(txHash);
		print("\tTransaction accepted by network!\n");
		return(True);

	def getTxReceipt(self, txHash, delay, maxRetries):
		for i in range(maxRetries):
			try: 
				receipt = self.web3.eth.getTransactionReceipt(txHash);
				print("Retrieved receipt!");
				return(receipt);
			except Exception as e:
				print(e);
				print("Transaction not found yet, will check again in", delay, "seconds");
				time.sleep(delay);
		self.ERROR("Transaction not found in", maxRetries, "retries.");
		return(False);


	# =====================
	# ====ERC20 methods====
	# =====================
	def erc20GetContract(self, tokenAddress):
		# Check to see if contract is already in cache
		if tokenAddress in self.erc20Contracts.keys():
			return(self.erc20Contracts[tokenAddress]);

		# Read files packaged in module
		abiPath = os.path.join('abi/ERC20.json');
		f = pkgutil.get_data(__name__, abiPath).decode();
		abi = json.loads(f);
		token = self.web3.eth.contract(tokenAddress, abi=abi)
		self.erc20Contracts[tokenAddress] = token;
		return(token);

	def erc20GetDecimals(self, tokenAddress):
		if tokenAddress in self.decimals.keys():
			return(self.decimals[tokenAddress]);
		token = self.erc20GetContract(tokenAddress);
		decimals = token.functions.decimals().call();
		self.decimals[tokenAddress] = decimals;
		return(decimals);

	def erc20GetBalanceNormalized(self, tokenAddress):
		token = self.erc20GetContract(tokenAddress);
		decimals = self.erc20GetDecimals(tokenAddress);
		normalizedBalance = token.functions.balanceOf(self.address).call() * 10**(-decimals);
		return(normalizedBalance);

	def erc20GetAllowanceNormalized(self, tokenAddress, allowedAddress):
		token = self.erc20GetContract(tokenAddress);
		decimals = self.erc20GetDecimals(tokenAddress);
		normalizedAllowance = token.functions.allowance(self.address,allowedAddress).call() * 10**(-decimals);
		return(normalizedAllowance);

	def erc20BuildFunctionSetAllowance(self, tokenAddress, allowedAddress, allowance):
		token = self.erc20GetContract(tokenAddress);
		approveFunction = token.functions.approve(allowedAddress, allowance);
		return(approveFunction);

	def erc20SignAndSendNewAllowance(	self,
										tokenAddress, 
										allowedAddress, 
										allowance,
										gasFactor,
										gasSpeed,
										nonceOverride=-1, 
										gasEstimateOverride=-1, 
										gasPriceGweiOverride=-1,
										isAsync=False):
		fn = self.erc20BuildFunctionSetAllowance(tokenAddress, allowedAddress, allowance);
		tx = self.buildTx(fn, gasFactor, gasSpeed, nonceOverride, gasEstimateOverride, gasPriceGweiOverride);
		txHash = self.sendTx(tx, isAsync);
		return(txHash);

	def erc20HasSufficientBalance(self, tokenAddress, amountToUse):
		balance = self.erc20GetBalanceNormalized(tokenAddress);
		print("Token:", tokenAddress);
		print("\tNeed:", amountToUse);
		print("\tWallet has:", balance);

		sufficient = balance > amountToUse;
		if not sufficient:
			self.ERROR("Insufficient Balance!");
		else:
			print("\tWallet has sufficient balance.");
		print();
		return(sufficient);
	
	def erc20HasSufficientBalances(self, poolDescription):
		tokenData = poolDescription["tokens"];
		tokens = list(tokenData.keys());
		sufficientBalance = True;
		for token in tokens:
			spendAmount = tokenData[token]["initialBalance"];
			currentHasSufficientBalance = self.erc20HasSufficientBalance(token, spendAmount);
			sufficientBalance &= currentHasSufficientBalance;
		return(sufficientBalance);

	def erc20HasSufficientAllowance(self, tokenAddress, allowedAddress):	
		currentAllowance = self.erc20GetAllowanceNormalized(tokenAddress, allowedAddress);
		balance = self.erc20GetBalanceNormalized(tokenAddress);

		print("Token:", tokenAddress);
		print("\tCurrent Allowance:", currentAllowance);
		print("\tCurrent Balance:", balance);

		sufficient = (currentAllowance >= balance);

		if not sufficient:
			print("\tInsufficient allowance!");
			print("\tWill need to unlock", tokenAddress);
		else:
			print("\tWallet has sufficient allowance.");
		print();
		return(sufficient);

	def erc20EnforceSufficientAllowance(self, 
										tokenAddress, 
										allowedAddress, 
										targetAllowance, 
										gasFactor,
										gasSpeed,
										nonceOverride, 
										gasEstimateOverride, 
										gasPriceGweiOverride,
										isAsync):
		if not self.erc20HasSufficientAllowance(tokenAddress, allowedAddress):
			if targetAllowance == -1:
				targetAllowance = self.INFINITE;
			print("Insufficient Allowance. Increasing allowance to", targetAllowance);
			txHash = self.erc20SignAndSendNewAllowance(tokenAddress, allowedAddress, targetAllowance, gasFactor, gasSpeed, nonceOverride=nonceOverride, isAsync=isAsync);
			return(txHash);
		return(None);

	def erc20EnforceSufficientVaultAllowance(self, tokenAddress, targetAllowance, gasFactor, gasSpeed, nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1, isAsync=False):
		return(self.erc20EnforceSufficientAllowance(tokenAddress, self.VAULT, targetAllowance, gasFactor, gasSpeed, nonceOverride, gasEstimateOverride, gasPriceGweiOverride, isAsync));

	def erc20AsyncEnforceSufficientVaultAllowances(self, poolDescription, gasFactor, gasSpeed, nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):
		nonce = self.web3.eth.get_transaction_count(self.web3.eth.default_account);
		txHashes = [];
		(tokens, checksumTokens) = self.balSortTokens(poolDescription);
		for token in tokens:
			targetAllowance = -1;
			if "allowance" in poolDescription["tokens"][token].keys():
				targetAllowance = poolDescription["tokens"][token]["allowance"];
			if targetAllowance == -1:
				targetAllowance = self.INFINITE;

			txHash = self.erc20EnforceSufficientVaultAllowance(token, targetAllowance, gasFactor, gasSpeed, nonceOverride=nonce, isAsync=True);
			if not txHash is None:
				txHashes.append(txHash);
				nonce += 1;
		
		for txHash in txHashes:
			self.waitForTx(txHash)
		return(True)

	# =====================
	# ====Etherscan Gas====
	# =====================
	def getGasPriceEtherscanGwei(self, speed):
		dt = (time.time() - self.lastEtherscanCallTime);
		if dt < 1.0/self.etherscanMaxRate:
			time.sleep((1.0/self.etherscanMaxRate - dt) * 1.1);

		if not speed in self.etherscanSpeedDict.keys():
			print("[ERROR] Speed entered is:", speed);
			print("\tSpeed must be 'slow', 'average', or 'fast'");
			return(False);

		response = requests.get("https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey=" + self.etherscanApiKey);
		self.lastEtherscanCallTime = time.time();
		return(response.json()["result"][self.etherscanSpeedDict[speed]]);

	def balSortTokens(self, poolData):
		tokensIn = poolData["tokens"];
		tokens = list(tokensIn.keys());
		tokens.sort();
		checksumTokens = [self.web3.toChecksumAddress(t) for t in tokens];
		return(tokens, checksumTokens);

	def balWeightsEqualOne(self, poolData):
		tokenData = poolData["tokens"];
		tokens = tokenData.keys();
		
		weightSum = 0.0;
		for token in tokens:
			weightSum += tokenData[token]["weight"];
		
		weightEqualsOne = (weightSum == 1.0)
		if not weightEqualsOne:
			self.ERROR("Token weights add up to " + str(weightSum) + ", but they must add up to 1.0");
		return(weightEqualsOne);

	def balNormalizeTokens(self, poolData, key):
		(tokens, checksumTokens) = self.balSortTokens(poolData);
		normalizedTokens = [];
		for token in tokens:
			decimals = self.erc20GetDecimals(token);
			rawValue = poolData["tokens"][token][key];
			normalized = int(rawValue * 10**decimals);
			normalizedTokens.append(normalized);
		return(normalizedTokens);

	def balGetFactoryContract(self, poolFactoryName):
		address = self.contractAddresses[poolFactoryName];
		abi = self.abis[poolFactoryName];
		factory = self.web3.eth.contract(address=address, abi=abi);
		return(factory);

	def balCreateFnWeightedPoolFactory(self, poolData):
		factory = self.balGetFactoryContract("WeightedPoolFactory");
		(tokens, checksumTokens) = self.balSortTokens(poolData);
		intWithDecimalsWeights = [int(poolData["tokens"][t]["weight"] * 1e18) for t in tokens];
		swapFeePercentage = int(poolData["swapFeePercent"] * 1e16);

		createFunction = factory.functions.create(	poolData["name"], 
													poolData["symbol"], 
													checksumTokens, 
													intWithDecimalsWeights, 
													swapFeePercentage, 
													self.ZERO_ADDRESS);
		return(createFunction);

	def balCreatePoolInFactory(self, poolFactoryName, poolDescription, gasFactor, gasPriceSpeed, nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):
		createFunction = None;
		
		# list of all supported pool factories
		# NOTE: when you add a pool factory to this list, be sure to
		# 		add it to the printout of supported factories below
		if poolFactoryName == "WeightedPoolFactory":
			createFunction = self.balCreateFnWeightedPoolFactory(poolDescription);
		if createFunction is None:
			print("No pool factory found with name:", poolFactoryName);
			print("Currently supported pool factories are:");
			print("\tWeightedPoolFactory");
			return(False);

		print("Pool function created, generating transaction...");
		tx = self.buildTx(createFunction, gasFactor, gasPriceSpeed, nonceOverride, gasEstimateOverride, gasPriceGweiOverride);
		print("Transaction Generated!");
		txHash = self.sendTx(tx);
		return(txHash);

	def balGetPoolIdFromHash(self, txHash):
		receipt = self.getTxReceipt(txHash, delay=2, maxRetries=5);
		
		# PoolRegistered event lives in the Vault
		vault = self.web3.eth.contract(address=self.VAULT, abi=self.abis["Vault"]);
		logs = vault.events.PoolRegistered().processReceipt(receipt);
		poolId = logs[0]['args']['poolId'].hex();
		print("\nDon't worry about that ^ warning, everything's fine :)");
		print("Your pool ID is:");
		print("\t0x" + str(poolId));
		return(poolId);

	def balRegisterPoolWithVault(self, poolDescription, poolId, gasFactor=1.05, gasPriceSpeed="average", nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):
		normalizedInitBalances = self.balNormalizeTokens(poolDescription, "initialBalance");
		JOIN_KIND_INIT = 0;
		initUserDataEncoded = eth_abi.encode_abi(	['uint256', 'uint256[]'], 
	                      							[JOIN_KIND_INIT, normalizedInitBalances]);
		(tokens, checksumTokens) = self.balSortTokens(poolDescription);
		joinPoolRequestTuple = (checksumTokens, normalizedInitBalances, initUserDataEncoded.hex(), poolDescription["fromInternalBalance"]);
		vault = self.web3.eth.contract(address=self.VAULT, abi=self.abis["Vault"]);
		joinPoolFunction = vault.functions.joinPool(poolId, 
												self.web3.toChecksumAddress(self.web3.eth.default_account), 
												self.web3.toChecksumAddress(self.web3.eth.default_account), 
												joinPoolRequestTuple);
		tx = self.buildTx(joinPoolFunction, gasFactor, gasPriceSpeed, nonceOverride, gasEstimateOverride, gasPriceGweiOverride);
		print("Transaction Generated!");		
		txHash = self.sendTx(tx);
		return(txHash);
