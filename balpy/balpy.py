# balpy.py

# python basics
import json
import os
import requests
import time
import sys
import pkgutil
from decimal import *

# web3 
from web3 import Web3
import eth_abi

from balpy import balancerErrors as be

class balpy(object):
	
	"""
	Balancer Protocol Python API
	Interface with Balancer V2 Smart contracts directly from Python
	"""

	DELEGATE_OWNER =	'0xBA1BA1ba1BA1bA1bA1Ba1BA1ba1BA1bA1ba1ba1B';
	ZERO_ADDRESS =  	'0x0000000000000000000000000000000000000000';

	# Constants
	INFINITE = 2 ** 256 - 1; #for infinite unlock

	# Environment variable names
	envVarEtherscan = 	"KEY_API_ETHERSCAN";
	envVarInfura = 		"KEY_API_INFURA";
	envVarPrivate = 	"KEY_PRIVATE";
	envVarCustomRPC = 	"BALPY_CUSTOM_RPC";
	
	# Etherscan API call management	
	lastEtherscanCallTime = 0;
	etherscanMaxRate = 5.0; #hz
	etherscanSpeedDict = {
			"slow":"SafeGasPrice",
			"average":"ProposeGasPrice",
			"fast":"FastGasPrice"
	};

	# Network parameters
	networkParams = {
						"mainnet":	{"id":1,		"blockExplorerUrl":"etherscan.io",					"balFrontend":"app.balancer.fi/#/"		},
						"ropsten":	{"id":3,		"blockExplorerUrl":"ropsten.etherscan.io"													},
						"rinkeby":	{"id":4,		"blockExplorerUrl":"rinkeby.etherscan.io"													},
						"goerli":	{"id":5,		"blockExplorerUrl":"goerli.etherscan.io"													},
						"kovan":	{"id":42,		"blockExplorerUrl":"kovan.etherscan.io",			"balFrontend":"kovan.app.balancer.fi/#/"},
						"polygon":	{"id":137,		"blockExplorerUrl":"polygonscan.com",				"balFrontend":"polygon.balancer.fi/#/"	},
						"arbitrum":	{"id":42161,	"blockExplorerUrl":"explorer.arbitrum.io",													}
					};

	# ABIs and Deployment Addresses
	abis = {};
	deploymentAddresses = {};
	contractDirectories = {
							"Vault": {
								"directory":"20210418-vault",
								"addressKey":"Vault"
							},
							"WeightedPoolFactory": {
								"directory":"20210418-weighted-pool",
								"addressKey":"WeightedPoolFactory"
							},
							"WeightedPool2TokensFactory": {
								"directory":"20210418-weighted-pool",
								"addressKey":"WeightedPool2TokensFactory"
							},
							"StablePoolFactory": {
								"directory":"20210624-stable-pool",
								"addressKey":"StablePoolFactory"
							},
							"LiquidityBootstrappingPoolFactory": {
								"directory":"20210721-liquidity-bootstrapping-pool",
								"addressKey":"LiquidityBootstrappingPoolFactory"
							},
							"MetaStablePoolFactory": {
								"directory":"20210727-meta-stable-pool",
								"addressKey":"MetaStablePoolFactory"
							}
						};

	decimals = {};
	erc20Contracts = {};

	UserBalanceOpKind = {
		"DEPOSIT_INTERNAL":0,
		"WITHDRAW_INTERNAL":1,
		"TRANSFER_INTERNAL":2,
		"TRANSFER_EXTERNAL":3
	};
	inverseUserBalanceOpKind = {
		0:"DEPOSIT_INTERNAL",
		1:"WITHDRAW_INTERNAL",
		2:"TRANSFER_INTERNAL",
		3:"TRANSFER_EXTERNAL"
	};
	JoinKind = {
		"INIT": 0,
		"EXACT_TOKENS_IN_FOR_BPT_OUT": 1,
		"TOKEN_IN_FOR_EXACT_BPT_OUT": 2
	}
	ExitKind = {
		"EXACT_BPT_IN_FOR_ONE_TOKEN_OUT": 0,
		"EXACT_BPT_IN_FOR_TOKENS_OUT": 1,
		"BPT_IN_FOR_EXACT_TOKENS_OUT": 2
	}

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
		self.network = network;

		# set high decimal precision
		getcontext().prec = 28;

		self.infuraApiKey = 		os.environ.get(self.envVarInfura);
		self.customRPC = 			os.environ.get(self.envVarCustomRPC);
		self.etherscanApiKey = 		os.environ.get(self.envVarEtherscan);
		self.privateKey =  			os.environ.get(self.envVarPrivate);

		if self.infuraApiKey is None and self.customRPC is None:
			self.ERROR("You need to add your KEY_API_INFURA or BALPY_CUSTOM_RPC environment variables\n");
			self.ERROR("!! If you are using L2, you must use BALPY_CUSTOM_RPC !!");
			print("\t\texport " + self.envVarInfura + "=<yourInfuraApiKey>");
			print("\t\t\tOR")
			print("\t\texport " + self.envVarCustomRPC + "=<yourCustomRPC>");
			print("\n\t\tNOTE: if you set " + self.envVarCustomRPC + ", it will override your Infura API key!")
			quit();

		if self.etherscanApiKey is None or self.privateKey is None:
			self.ERROR("You need to add your keys to the your environment variables");
			print("\t\texport " + self.envVarEtherscan + "=<yourEtherscanApiKey>");
			print("\t\texport " + self.envVarPrivate + "=<yourPrivateKey>");
			quit();

		endpoint = self.customRPC;
		if endpoint is None:
			endpoint = 'https://' + self.network + '.infura.io/v3/' + self.infuraApiKey;

		self.web3 = Web3(Web3.HTTPProvider(endpoint));
		acct = self.web3.eth.account.privateKeyToAccount(self.privateKey);
		self.web3.eth.default_account = acct.address;
		self.address = acct.address;

		if self.verbose:
			print("Initialized account", self.web3.eth.default_account);
			print("Connected to web3 at", endpoint);

		for contractType in self.contractDirectories.keys():
			subdir = self.contractDirectories[contractType]["directory"];
			addressKey = self.contractDirectories[contractType]["addressKey"];

			# get contract abi from deployment
			abiPath = os.path.join('deployments', subdir , "abi", contractType + '.json');
			try:
				f = pkgutil.get_data(__name__, abiPath).decode();
				currAbi = json.loads(f);

				self.abis[contractType] = currAbi;
			except BaseException as error:
				self.ERROR('Error accessing file: {}'.format(abiPath))
				self.ERROR('{}'.format(error))

			# get deployment address for given network
			deploymentPath = os.path.join('deployments', subdir, "output", self.network + '.json');
			try:
				f = pkgutil.get_data(__name__, deploymentPath).decode();
				currData = json.loads(f);
				currAddress = currData[addressKey];
				self.deploymentAddresses[contractType] = currAddress;
			except BaseException as error:
				self.ERROR('{} not found for network {}'.format(contractType, self.network))
				self.ERROR('{}'.format(error))

		print("Available contracts on", self.network)
		for element in self.deploymentAddresses.keys():
			address = self.deploymentAddresses[element];
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
			try:
				gasEstimate = int(fn.estimateGas() * gasFactor);
			except BaseException as error:
				descriptiveError = be.handleException(error);
				self.ERROR("Transaction failed at gas estimation!");
				self.ERROR(descriptiveError);
				return(None);

		# Get gas price from Etherscan if not overridden
		if gasPriceGweiOverride > -1:
			gasPriceGwei = gasPriceGweiOverride;
		else:
			#rinkeby, kovan gas strategy
			if chainIdNetwork in [4, 42]:
				gasPriceGwei = 2;

			# polygon gas strategy
			elif chainIdNetwork == 137:
				gasPriceGwei = self.getGasPricePolygon(gasSpeed);

			#mainnet gas strategy
			else:
				gasPriceGwei = self.getGasPriceEtherscanGwei(gasSpeed);
		
		print("\tGas Estimate:\t", gasEstimate);
		print("\tGas Price:\t", gasPriceGwei, "Gwei");
		print("\tNonce:\t\t", nonce);

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

		print();
		print("Sending transaction, view progress at:");
		print("\thttps://"+self.networkParams[self.network]["blockExplorerUrl"]+"/tx/"+txHash);
		
		if not isAsync:
			self.waitForTx(txHash);
		return(txHash);

	def waitForTx(self, txHash, timeOutSec=120):
		txSuccessful = True;
		print();
		print("Waiting for tx:", txHash);
		try:
			receipt = self.web3.eth.wait_for_transaction_receipt(txHash, timeout=timeOutSec);
			if not receipt["status"] == 1:
				txSuccessful = False;
		except BaseException as error:
			print('Transaction timeout: {}'.format(error))
			return(False);

		# Race condition: add a small delay to avoid getting the last nonce
		time.sleep(0.5);

		print("\tTransaction accepted by network!");
		if not txSuccessful:
			self.ERROR("Transaction failed!")
			return(False)
		print("\tTransaction was successful!\n");

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
		token = self.web3.eth.contract(self.web3.toChecksumAddress(tokenAddress), abi=abi)
		self.erc20Contracts[tokenAddress] = token;
		return(token);

	def erc20GetDecimals(self, tokenAddress):
		if tokenAddress in self.decimals.keys():
			return(self.decimals[tokenAddress]);
		if tokenAddress == self.ZERO_ADDRESS:
			self.decimals[tokenAddress] = 18;
			return(18);
		token = self.erc20GetContract(tokenAddress);
		decimals = token.functions.decimals().call();
		self.decimals[tokenAddress] = decimals;
		return(decimals);

	def erc20GetBalanceStandard(self, tokenAddress, address=None):
		if address is None:
			address = self.address;
		token = self.erc20GetContract(tokenAddress);
		decimals = self.erc20GetDecimals(tokenAddress);
		standardBalance = Decimal(token.functions.balanceOf(address).call()) * Decimal(10**(-decimals));
		return(standardBalance);

	def erc20GetAllowanceStandard(self, tokenAddress, allowedAddress):
		token = self.erc20GetContract(tokenAddress);
		decimals = self.erc20GetDecimals(tokenAddress);
		standardAllowance = Decimal(token.functions.allowance(self.address,allowedAddress).call()) * Decimal(10**(-decimals));
		return(standardAllowance);

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
		balance = self.erc20GetBalanceStandard(tokenAddress);

		print("Token:", tokenAddress);
		print("\tNeed:", float(amountToUse));
		print("\tWallet has:", float(balance));

		sufficient = (float(balance) >= float(amountToUse));
		if not sufficient:
			self.ERROR("Insufficient Balance!");
		else:
			print("\tWallet has sufficient balance.");
		print();
		return(sufficient);
	
	def erc20HasSufficientBalances(self, tokens, amounts):
		if not len(tokens) == len(amounts):
			self.ERROR("Array length mismatch with " + str(len(tokens)) + " tokens and " + str(len(amounts)) + " amounts.");
			return(False);
		numElements = len(tokens);
		sufficientBalance = True;
		for i in range(numElements):
			token = tokens[i];
			amount = amounts[i];
			currentHasSufficientBalance = self.erc20HasSufficientBalance(token, amount);
			sufficientBalance &= currentHasSufficientBalance;
		return(sufficientBalance);

	def erc20HasSufficientAllowance(self, tokenAddress, allowedAddress, amount):
		currentAllowance = self.erc20GetAllowanceStandard(tokenAddress, allowedAddress);
		balance = self.erc20GetBalanceStandard(tokenAddress);

		print("Token:", tokenAddress);
		print("\tCurrent Allowance:", currentAllowance);
		print("\tCurrent Balance:", balance);
		print("\tAmount to Spend:", amount);

		sufficient = (currentAllowance >= Decimal(amount));

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
										amount,
										gasFactor,
										gasSpeed,
										nonceOverride,
										gasEstimateOverride,
										gasPriceGweiOverride,
										isAsync):
		if not self.erc20HasSufficientAllowance(tokenAddress, allowedAddress, amount):
			if targetAllowance == -1 or targetAllowance == self.INFINITE:
				targetAllowance = self.INFINITE;
			else:
				decimals = self.erc20GetDecimals(tokenAddress);
				targetAllowance = Decimal(targetAllowance) * Decimal(10**decimals);
			targetAllowance = int(targetAllowance);
			print("Insufficient Allowance: Increasing to", targetAllowance);
			txHash = self.erc20SignAndSendNewAllowance(tokenAddress, allowedAddress, targetAllowance, gasFactor, gasSpeed, nonceOverride=nonceOverride, isAsync=isAsync);
			return(txHash);
		return(None);

	def erc20EnforceSufficientVaultAllowance(self, tokenAddress, targetAllowance, amount, gasFactor, gasSpeed, nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1, isAsync=False):
		return(self.erc20EnforceSufficientAllowance(tokenAddress, self.deploymentAddresses["Vault"], targetAllowance, amount, gasFactor, gasSpeed, nonceOverride, gasEstimateOverride, gasPriceGweiOverride, isAsync));

	def erc20GetTargetAllowancesFromPoolData(self, poolDescription):
		(tokens, checksumTokens) = self.balSortTokens(list(poolDescription["tokens"].keys()));
		allowances = [];
		for token in tokens:
			targetAllowance = -1;
			if "allowance" in poolDescription["tokens"][token].keys():
				targetAllowance = poolDescription["tokens"][token]["allowance"];
			if targetAllowance == -1:
				targetAllowance = self.INFINITE;
			allowances.append(targetAllowance);
		return(tokens, allowances);

	def erc20AsyncEnforceSufficientVaultAllowances(self, tokens, targetAllowances, amounts, gasFactor, gasSpeed, nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):
		if not len(tokens) == len(targetAllowances):
			self.ERROR("Array length mismatch with " + str(len(tokens)) + " tokens and " + str(len(targetAllowances)) + " targetAllowances.");
			return(False);

		nonce = self.web3.eth.get_transaction_count(self.web3.eth.default_account);
		txHashes = [];
		numElements = len(tokens);
		for i in range(numElements):
			token = tokens[i];
			targetAllowance = targetAllowances[i];
			amount = amounts[i];
			txHash = self.erc20EnforceSufficientVaultAllowance(token, targetAllowance, amount, gasFactor, gasSpeed, nonceOverride=nonce, isAsync=True);
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
			self.ERROR("Speed entered is:" + speed);
			print("\tSpeed must be 'slow', 'average', or 'fast'");
			return(False);

		response = requests.get("https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey=" + self.etherscanApiKey);
		self.lastEtherscanCallTime = time.time();
		return(response.json()["result"][self.etherscanSpeedDict[speed]]);

	def getGasPricePolygon(self, speed):
		allowedSpeeds = ["safeLow","standard","fast","fastest"];
		if speed not in allowedSpeeds:
			self.ERROR("Speed entered is:" + speed);
			self.ERROR("Speed must be one of the following options:");
			for s in allowedSpeeds:
				print("\t" + s);
			return(False);

		r = requests.get("https://gasstation-mainnet.matic.network/")
		prices = r.json();
		return(prices[speed]);

	def balSortTokens(self, tokensIn):
		# tokens need to be sorted as lowercase, but if they're provided as checksum, then
		# the checksum format strings are still the keys outside of this function, so they
		# must be preserved as they're input
		lowerTokens = [t.lower() for t in tokensIn];
		lowerToOriginal = {};
		for i in range(len(tokensIn)):
			lowerToOriginal[lowerTokens[i]] = tokensIn[i];
		lowerTokens.sort();

		# get checksum tokens, translated sorted lower tokens back to their original format
		checksumTokens = [self.web3.toChecksumAddress(t) for t in lowerTokens];
		sortedInputTokens = [lowerToOriginal[f] for f in lowerTokens]

		return(sortedInputTokens, checksumTokens);

	def balWeightsEqualOne(self, poolData):
		tokenData = poolData["tokens"];
		tokens = tokenData.keys();
		
		weightSum = Decimal(0.0);
		for token in tokens:
			weightSum += Decimal(tokenData[token]["weight"]);
		
		weightEqualsOne = (weightSum == Decimal(1.0));
		if not weightEqualsOne:
			self.ERROR("Token weights add up to " + str(weightSum) + ", but they must add up to 1.0");
			self.ERROR("If you are passing more than 16 digits of precision, you must pass the value as a string")
		return(weightEqualsOne);

	def balConvertTokensToWei(self, tokens, amounts):
		rawTokens = [];
		if not len(tokens) == len(amounts):
			self.ERROR("Array length mismatch with " + str(len(tokens)) + " tokens and " + str(len(amounts)) + " amounts.");
			return(False);
		numElements = len(tokens);
		for i in range(numElements):
			token = tokens[i];
			rawValue = amounts[i];
			decimals = self.erc20GetDecimals(token);
			raw = int(Decimal(rawValue) * Decimal(10**decimals));
			rawTokens.append(raw);
		return(rawTokens);

	def balGetFactoryContract(self, poolFactoryName):
		address = self.deploymentAddresses[poolFactoryName];
		abi = self.abis[poolFactoryName];
		factory = self.web3.eth.contract(address=address, abi=abi);
		return(factory);

	def balSetOwner(self, poolData):
		owner = self.ZERO_ADDRESS;
		if "owner" in poolData.keys():
			ownerAddress = poolData["owner"];
			if not len(ownerAddress) == 42:
				self.ERROR("Entry for \"owner\" must be a 42 character Ethereum address beginning with \"0x\"");
				return(False);
			owner = self.web3.toChecksumAddress(ownerAddress);
		return(owner);

	def balCreateFnWeightedPoolFactory(self, poolData):
		factory = self.balGetFactoryContract("WeightedPoolFactory");
		(tokens, checksumTokens) = self.balSortTokens(list(poolData["tokens"].keys()));

		intWithDecimalsWeights = [int(Decimal(poolData["tokens"][t]["weight"]) * Decimal(1e18)) for t in tokens];
		swapFeePercentage = int(Decimal(poolData["swapFeePercent"]) * Decimal(1e16));

		if not self.balWeightsEqualOne(poolData):
			return(False);

		owner = self.balSetOwner(poolData);

		createFunction = factory.functions.create(	poolData["name"], 
													poolData["symbol"], 
													checksumTokens, 
													intWithDecimalsWeights, 
													swapFeePercentage, 
													owner);
		return(createFunction);

	def balCreateFnWeightedPool2TokensFactory(self, poolData):
		factory = self.balGetFactoryContract("WeightedPool2TokensFactory");
		(tokens, checksumTokens) = self.balSortTokens(list(poolData["tokens"].keys()));
		
		if not len(tokens) == 2:
			self.ERROR("WeightedPool2TokensFactory requires 2 tokens, but", len(tokens), "were given.");
			return(False);

		if not self.balWeightsEqualOne(poolData):
			return(False);

		intWithDecimalsWeights = [int(Decimal(poolData["tokens"][t]["weight"]) * Decimal(1e18)) for t in tokens];
		swapFeePercentage = int(Decimal(poolData["swapFeePercent"]) * Decimal(1e16));

		owner = self.balSetOwner(poolData);

		oracleEnabled = False;
		if "oracleEnabled" in poolData.keys():
			oracleEnabled = poolData["oracleEnabled"];
			if isinstance(oracleEnabled, str):
				if oracleEnabled.lower() == "true":
					oracleEnabled = True;
				else:
					oracleEnabled = False;

		createFunction = factory.functions.create(	poolData["name"],
													poolData["symbol"],
													checksumTokens,
													intWithDecimalsWeights,
													swapFeePercentage,
													oracleEnabled,
													owner);
		return(createFunction);

	def balCreateFnStablePoolFactory(self, poolData):
		factory = self.balGetFactoryContract("StablePoolFactory");
		(tokens, checksumTokens) = self.balSortTokens(list(poolData["tokens"].keys()));
		swapFeePercentage = int(poolData["swapFeePercent"] * 1e16);

		owner = self.balSetOwner(poolData);

		createFunction = factory.functions.create(	poolData["name"],
													poolData["symbol"],
													checksumTokens,
													poolData["amplificationParameter"],
													swapFeePercentage,
													owner);
		return(createFunction);

	def balCreateFnLBPoolFactory(self, poolData):
		factory = self.balGetFactoryContract("LiquidityBootstrappingPoolFactory");
		(tokens, checksumTokens) = self.balSortTokens(list(poolData["tokens"].keys()));

		if not self.balWeightsEqualOne(poolData):
			return(False);

		swapFeePercentage = int(poolData["swapFeePercent"] * 1e16);
		intWithDecimalsWeights = [int(Decimal(poolData["tokens"][t]["weight"]) * Decimal(1e18)) for t in tokens];
		owner = self.balSetOwner(poolData);

		if not owner == self.address:
			self.WARN("!!! You are not the owner for your LBP !!!")
			self.WARN("You:\t\t" + self.address)
			self.WARN("Pool Owner:\t" + owner)

			print();
			self.WARN("Only the pool owner can add liquidity. If you do not control " + owner + " then you will not be able to add liquidity!")
			self.WARN("If you DO control " + owner + ", you will need to use the \"INIT\" join type from that address")
			cancelTimeSec = 30;
			self.WARN("If the owner mismatch is was unintentional, you have " + str(cancelTimeSec) + " seconds to cancel with Ctrl+C.")
			time.sleep(cancelTimeSec);

		createFunction = factory.functions.create(	poolData["name"],
													poolData["symbol"],
													checksumTokens,
													intWithDecimalsWeights,
													swapFeePercentage,
													owner,
													poolData["swapEnabledOnStart"]);
		return(createFunction);

	def balCreateFnMetaStablePoolFactory(self, poolData):
		factory = self.balGetFactoryContract("MetaStablePoolFactory");
		(tokens, checksumTokens) = self.balSortTokens(list(poolData["tokens"].keys()));
		swapFeePercentage = int(poolData["swapFeePercent"] * 1e16);
		owner = self.balSetOwner(poolData);

		rateProviders = [poolData["tokens"][token]["rateProvider"] for token in tokens]
		priceRateCacheDurations = [poolData["tokens"][token]["priceRateCacheDuration"] for token in tokens]

		createFunction = factory.functions.create(	poolData["name"],
													poolData["symbol"],
													checksumTokens,
													poolData["amplificationParameter"],
													rateProviders,
													priceRateCacheDurations,
													swapFeePercentage,
													poolData["oracleEnabled"],
													owner);
		return(createFunction);

	def balCreatePoolInFactory(self, poolDescription, gasFactor, gasPriceSpeed, nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):
		createFunction = None;
		poolFactoryName = poolDescription["poolType"] + "Factory";

		# list of all supported pool factories
		# NOTE: when you add a pool factory to this list, be sure to
		# 		add it to the printout of supported factories below
		if poolFactoryName == "WeightedPoolFactory":
			createFunction = self.balCreateFnWeightedPoolFactory(poolDescription);
		if poolFactoryName == "WeightedPool2TokensFactory":
			createFunction = self.balCreateFnWeightedPool2TokensFactory(poolDescription);
		if poolFactoryName == "StablePoolFactory":
			createFunction = self.balCreateFnStablePoolFactory(poolDescription);
		if poolFactoryName == "LiquidityBootstrappingPoolFactory":
			createFunction = self.balCreateFnLBPoolFactory(poolDescription);
		if poolFactoryName == "MetaStablePoolFactory":
			createFunction = self.balCreateFnMetaStablePoolFactory(poolDescription);
		if createFunction is None:
			print("No pool factory found with name:", poolFactoryName);
			print("Currently supported pool types are:");
			print("\tWeightedPool");
			print("\tWeightedPool2Token");
			print("\tStablePool");
			print("\tLiquidityBootstrappingPool");
			print("\tMetaStablePool");
			return(False);

		if not createFunction:
			self.ERROR("Pool creation failed.")
			return(False)
		print("Pool function created, generating transaction...");
		tx = self.buildTx(createFunction, gasFactor, gasPriceSpeed, nonceOverride, gasEstimateOverride, gasPriceGweiOverride);
		print("Transaction Generated!");
		txHash = self.sendTx(tx);
		return(txHash);

	def balGetPoolIdFromHash(self, txHash):
		receipt = self.getTxReceipt(txHash, delay=2, maxRetries=5);
		
		# PoolRegistered event lives in the Vault
		vault = self.web3.eth.contract(address=self.deploymentAddresses["Vault"], abi=self.abis["Vault"]);
		logs = vault.events.PoolRegistered().processReceipt(receipt);
		poolId = logs[0]['args']['poolId'].hex();
		self.GOOD("\nDon't worry about that ^ warning, everything's fine :)");
		print("Your pool ID is:");
		print("\t0x" + str(poolId));
		return(poolId);

	def balJoinPoolExactIn(self, joinDescription, gasFactor=1.05, gasPriceSpeed="average", nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):
		(sortedTokens, checksumTokens) = self.balSortTokens(list(joinDescription["tokens"].keys()));
		amountsBySortedTokens = [joinDescription["tokens"][token]["amount"] for token in sortedTokens];
		rawAmounts = self.balConvertTokensToWei(sortedTokens, amountsBySortedTokens);

		userDataEncoded = eth_abi.encode_abi(	['uint256', 'uint256[]'],
												[self.JoinKind["EXACT_TOKENS_IN_FOR_BPT_OUT"], rawAmounts]);
		joinPoolRequestTuple = (checksumTokens, rawAmounts, userDataEncoded.hex(), joinDescription["fromInternalBalance"]);
		vault = self.web3.eth.contract(address=self.deploymentAddresses["Vault"], abi=self.abis["Vault"]);
		joinPoolFunction = vault.functions.joinPool(joinDescription["poolId"],
												self.web3.toChecksumAddress(self.web3.eth.default_account),
												self.web3.toChecksumAddress(self.web3.eth.default_account),
												joinPoolRequestTuple);
		tx = self.buildTx(joinPoolFunction, gasFactor, gasPriceSpeed, nonceOverride, gasEstimateOverride, gasPriceGweiOverride);
		print("Transaction Generated!");
		txHash = self.sendTx(tx);
		return(txHash);

	def balRegisterPoolWithVault(self, poolDescription, poolId, gasFactor=1.05, gasPriceSpeed="average", nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):
		self.WARN("\"balRegisterPoolWithVault\" is deprecated. Please use \"balJoinPoolInit\".")
		self.balJoinPoolInit(poolDescription, poolId, gasFactor, gasPriceSpeed, nonceOverride, gasEstimateOverride, gasPriceGweiOverride)

	def balJoinPoolInit(self, poolDescription, poolId, gasFactor=1.05, gasPriceSpeed="average", nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):

		(sortedTokens, checksumTokens) = self.balSortTokens(list(poolDescription["tokens"].keys()));
		initialBalancesBySortedTokens = [poolDescription["tokens"][token]["initialBalance"] for token in sortedTokens];

		rawInitBalances = self.balConvertTokensToWei(sortedTokens, initialBalancesBySortedTokens);
		initUserDataEncoded = eth_abi.encode_abi(	['uint256', 'uint256[]'], 
													[self.JoinKind["INIT"], rawInitBalances]);

		#todo replace this code with a join call
		joinPoolRequestTuple = (checksumTokens, rawInitBalances, initUserDataEncoded.hex(), poolDescription["fromInternalBalance"]);
		vault = self.web3.eth.contract(address=self.deploymentAddresses["Vault"], abi=self.abis["Vault"]);
		joinPoolFunction = vault.functions.joinPool(poolId, 
												self.web3.toChecksumAddress(self.web3.eth.default_account), 
												self.web3.toChecksumAddress(self.web3.eth.default_account), 
												joinPoolRequestTuple);
		tx = self.buildTx(joinPoolFunction, gasFactor, gasPriceSpeed, nonceOverride, gasEstimateOverride, gasPriceGweiOverride);
		print("Transaction Generated!");		
		txHash = self.sendTx(tx);
		return(txHash);

	def balVaultWeth(self):
		vault = self.web3.eth.contract(address=self.deploymentAddresses["Vault"], abi=self.abis["Vault"]);
		wethAddress = vault.functions.WETH().call();
		return(wethAddress);

	def balVaultGetInternalBalance(self, tokens, address=None):
		if address is None:
			address = self.web3.eth.default_account;

		vault = self.web3.eth.contract(address=self.deploymentAddresses["Vault"], abi=self.abis["Vault"]);
		(sortedTokens, checksumTokens) = self.balSortTokens(tokens);
		balances = vault.functions.getInternalBalance(address, checksumTokens).call();
		numElements = len(sortedTokens);
		internalBalances = {};
		for i in range(numElements):
			token = checksumTokens[i];
			decimals = self.erc20GetDecimals(token);
			internalBalances[token] = Decimal(balances[i]) * Decimal(10**(-decimals));
		return(internalBalances);

	def balVaultDoManageUserBalance(self, kind, token, amount, sender, recipient, isAsync=False, gasFactor=1.05, gasPriceSpeed="average", nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):
		if self.verbose:
			print("Managing User Balance");
			print("\tKind:\t\t", self.inverseUserBalanceOpKind[kind]);
			print("\tToken:\t\t", str(token));
			print("\tAmount:\t\t", str(amount));
			print("\tSender:\t\t", str(sender));
			print("\tRecipient:\t", str(recipient));
		manageUserBalanceFn = self.balVaultBuildManageUserBalanceFn(kind, token, amount, sender, recipient);

		print();
		print("Building ManageUserBalance");
		tx = self.buildTx(manageUserBalanceFn, gasFactor, gasPriceSpeed, nonceOverride, gasEstimateOverride, gasPriceGweiOverride);
		txHash = self.sendTx(tx, isAsync);
		return(txHash);

	def balVaultBuildManageUserBalanceFn(self, kind, token, amount, sender, recipient):
		kind = kind;
		asset = self.web3.toChecksumAddress(token);
		amount = self.balConvertTokensToWei([token],[amount])[0];
		sender = self.web3.toChecksumAddress(sender);
		recipient = self.web3.toChecksumAddress(recipient);
		inputTupleList = [(kind, asset, amount, sender, recipient)];

		vault = self.web3.eth.contract(address=self.deploymentAddresses["Vault"], abi=self.abis["Vault"]);
		manageUserBalanceFn = vault.functions.manageUserBalance(inputTupleList);
		return(manageUserBalanceFn);

	def balSwapIsFlashSwap(self, swapDescription):
		for amount in swapDescription["limits"]:
			if not float(amount) == 0.0:
				return(False);
		return(True);

	def balReorderTokenDicts(self, tokens):
		originalIdxToSortedIdx = {};
		sortedIdxToOriginalIdx = {};
		tokenAddressToIdx = {};
		for i in range(len(tokens)):
			tokenAddressToIdx[tokens[i]] = i;
		sortedTokens = tokens;
		sortedTokens.sort();
		for i in range(len(sortedTokens)):
			originalIdxToSortedIdx[tokenAddressToIdx[sortedTokens[i]]] = i;
			sortedIdxToOriginalIdx[i] = tokenAddressToIdx[sortedTokens[i]];
		return(sortedTokens, originalIdxToSortedIdx, sortedIdxToOriginalIdx);

	def balSwapGetUserData(self, poolType):
		userDataNull = eth_abi.encode_abi(['uint256'], [0]);
		userData = userDataNull;
		#for weightedPools, user data is just null, but in the future there may be userData to pass to pools for swaps
		# if poolType == "someFuturePool":
		# 	userData = "something else";
		return(userData);

	def balDoBatchSwap(self, swapDescription, isAsync=False, gasFactor=1.05, gasPriceSpeed="average", nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):
		batchSwapFn = self.balCreateFnBatchSwap(swapDescription);
		tx = self.buildTx(batchSwapFn, gasFactor, gasPriceSpeed, nonceOverride, gasEstimateOverride, gasPriceGweiOverride);
		txHash = self.sendTx(tx, isAsync);
		return(txHash);

	def balCreateFnBatchSwap(self, swapDescription):
		(sortedTokens, originalIdxToSortedIdx, sortedIdxToOriginalIdx) = self.balReorderTokenDicts(swapDescription["assets"]);
		numTokens = len(sortedTokens);

		# reorder the limits to refer to properly sorted tokens
		reorderedLimits = [];
		for i in range(numTokens):
			currLimitStandard = float(swapDescription["limits"][sortedIdxToOriginalIdx[i]]);
			decimals = self.erc20GetDecimals(sortedTokens[i]);
			currLimitRaw = int(Decimal(currLimitStandard) * Decimal(10**(decimals)))
			reorderedLimits.append(currLimitRaw)

		kind = int(swapDescription["kind"]);
		assets = [self.web3.toChecksumAddress(token) for token in sortedTokens];

		swapsTuples = [];
		for swap in swapDescription["swaps"]:
			idxSortedIn = originalIdxToSortedIdx[int(swap["assetInIndex"])];
			idxSortedOut = originalIdxToSortedIdx[int(swap["assetOutIndex"])];
			decimals = self.erc20GetDecimals(sortedTokens[idxSortedIn]);
			amount = int( Decimal(swap["amount"]) * Decimal(10**(decimals)) );

			swapsTuple = (	swap["poolId"],
							idxSortedIn,
							idxSortedOut,
							amount,
							self.balSwapGetUserData(None));
			swapsTuples.append(swapsTuple);

		funds = (	self.web3.toChecksumAddress(swapDescription["funds"]["sender"]),
					swapDescription["funds"]["fromInternalBalance"],
					self.web3.toChecksumAddress(swapDescription["funds"]["recipient"]),
					swapDescription["funds"]["toInternalBalance"]);
		intReorderedLimits = [int(element) for element in reorderedLimits];
		deadline = int(swapDescription["deadline"]);
		vault = self.web3.eth.contract(address=self.deploymentAddresses["Vault"], abi=self.abis["Vault"]);
		batchSwapFunction = vault.functions.batchSwap(	kind,
														swapsTuples,
														assets,
														funds,
														intReorderedLimits,
														deadline);
		return(batchSwapFunction);

	def balGetLinkToFrontend(self, poolId):
		if "balFrontend" in self.networkParams[self.network].keys():
			return("https://" + self.networkParams[self.network]["balFrontend"] + "pool/0x" + poolId);
		else:
			return("")


