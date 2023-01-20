# balpy.py

# python basics
import copy
import json
import os
import requests
import time
import sys
import pkgutil
from decimal import *
from functools import cache
import traceback

# low level web3
from web3 import Web3, middleware
from web3.gas_strategies.time_based import glacial_gas_price_strategy, slow_gas_price_strategy, medium_gas_price_strategy, fast_gas_price_strategy
from web3.middleware import geth_poa_middleware
from web3._utils.abi import get_abi_output_types
import eth_abi

# high level web3
from multicaller import multicaller

# balpy modules
from . import balancerErrors as be
from .enums.stablePoolJoinExitKind import StablePoolJoinKind, StablePhantomPoolJoinKind, StablePoolExitKind
from .enums.weightedPoolJoinExitKind import WeightedPoolJoinKind, WeightedPoolExitKind

class Suppressor(object):
    def __enter__(self):
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
    def __exit__(self, type, value, traceback):
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        if type is not None:
            a=0;
            # Do normal exception handling
    def write(self, x): pass

def getLongestStringLength(array):
	maxLength = 0;
	for a in array:
		if len(a) > maxLength:
			maxLength = len(a);
	return(maxLength);

def padWithSpaces(myString, endLength):
	stringLength = len(myString);
	extraSpace = endLength - stringLength;

	outputString = myString + "".join([" "]*extraSpace);
	return(outputString);

class balpy(object):
	
	"""
	Balancer Protocol Python API
	Interface with Balancer V2 Smart contracts directly from Python
	"""

	DELEGATE_OWNER =	'0xBA1BA1ba1BA1bA1bA1Ba1BA1ba1BA1bA1ba1ba1B';
	ZERO_ADDRESS =  	'0x0000000000000000000000000000000000000000';

	# Constants
	INFINITE = 2 ** 256 - 1; #for infinite unlock
	MAX_UINT_112 = 2**112 - 1; #for stablephantom max bpt


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
	speedDict = {
			"glacial":glacial_gas_price_strategy,
			"slow":slow_gas_price_strategy,
			"average":medium_gas_price_strategy,
			"fast":fast_gas_price_strategy
	}

	# Network parameters
	networkParams = {
						"mainnet":	{"id":1,		"blockExplorerUrl":"etherscan.io",					"balFrontend":"app.balancer.fi/#/"		},
						"ropsten":	{"id":3,		"blockExplorerUrl":"ropsten.etherscan.io"													},
						"rinkeby":	{"id":4,		"blockExplorerUrl":"rinkeby.etherscan.io"													},
						"goerli":	{"id":5,		"blockExplorerUrl":"goerli.etherscan.io"													},
						"optimism":	{"id":10,		"blockExplorerUrl":"optimistic.etherscan.io"													},
						"kovan":	{"id":42,		"blockExplorerUrl":"kovan.etherscan.io",			"balFrontend":"kovan.balancer.fi/#/"	},
						"polygon":	{"id":137,		"blockExplorerUrl":"polygonscan.com",				"balFrontend":"polygon.balancer.fi/#/"	},
						"fantom":	{"id":250,		"blockExplorerUrl":"ftmscan.com",					"balFrontend":"app.beets.fi/#/"			},
						"arbitrum":	{"id":42161,	"blockExplorerUrl":"arbiscan.io",					"balFrontend":"arbitrum.balancer.fi/#/"	}
					};

	# ABIs and Deployment Addresses
	abis = {};
	deploymentAddresses = {};
	contractDirectories = {
							# ===== Vault Infra =====
							"Vault": {
								"directory":"20210418-vault"
							},
							"BalancerHelpers": {
								"directory":"20210418-vault"
							},
							"Authorizer": {
								"directory":"20210418-authorizer"
							},

							# ====== Pools and Associated Contracts ======
							"WeightedPoolFactory": {
								"directory":"20220908-weighted-pool-v2"
							},
							"WeightedPool2TokensFactory": {
								"directory":"20210418-weighted-pool"
							},
							"StablePoolFactory": {
								"directory":"20220609-stable-pool-v2"
							},
							"LiquidityBootstrappingPoolFactory": {
								"directory":"20210721-liquidity-bootstrapping-pool"
							},
							"MetaStablePoolFactory": {
								"directory":"20210727-meta-stable-pool"
							},
							"WstETHRateProvider": {
								"directory":"20210812-wsteth-rate-provider"
							},
							"InvestmentPoolFactory": {
								"directory":"20210907-investment-pool"
							},
							"StablePhantomPoolFactory": {
								"directory":"20211208-stable-phantom-pool"
							},
							"ComposableStablePoolFactory": {
								"directory":"20220906-composable-stable-pool"
							},
							"AaveLinearPoolFactory": {
								"directory":"20220817-aave-rebalanced-linear-pool"
							},
							"ERC4626LinearPoolFactory": {
								"directory":"20220304-erc4626-linear-pool"
							},
							"NoProtocolFeeLiquidityBootstrappingPoolFactory": {
								"directory":"20211202-no-protocol-fee-lbp"
							},
							"ManagedPoolFactory": {
								"directory":"20221021-managed-pool"
							},

							# ===== Relayers and Infra =====
							# TODO: update dir to 20220318-batch-relayer-v2 once deployed on all networks
							"BalancerRelayer": {
								"directory":"20211203-batch-relayer"
							},
							"BatchRelayerLibrary": {
								"directory":"20211203-batch-relayer"
							},
							"LidoRelayer": {
								"directory":"20210812-lido-relayer"
							},

							# ===== Liquidity Mining Infra =====
							"MerkleRedeem": {
								"directory":"20210811-ldo-merkle"
							},
							"MerkleOrchard": {
								"directory":"20211012-merkle-orchard"
							},

							# ===== Gauges and Infra =====
							"AuthorizerAdaptor": {
								"directory":"20220325-authorizer-adaptor"
							},
							"BALTokenHolderFactory": {
								"directory":"20220325-bal-token-holder-factory"
							},
							"BalancerTokenAdmin": {
								"directory":"20220325-balancer-token-admin"
							},
							"GaugeAdder": {
								"directory":"20220325-gauge-adder"
							},
							"VotingEscrow": {
								"directory":"20220325-gauge-controller"
							},
							"GaugeController": {
								"directory":"20220325-gauge-controller"
							},
							"BalancerMinter": {
								"directory":"20220325-gauge-controller"
							},
							"LiquidityGaugeFactory": {
								"directory":"20220325-mainnet-gauge-factory"
							},
							"SingleRecipientGaugeFactory": {
								"directory":"20220325-single-recipient-gauge-factory"
							},
							"VotingEscrowDelegation": {
								"directory":"20220325-ve-delegation"
							},
							"VotingEscrowDelegationProxy": {
								"directory":"20220325-ve-delegation"
							},
							"veBALDeploymentCoordinator": {
								"directory":"20220325-veBAL-deployment-coordinator"
							},
							"ArbitrumRootGaugeFactory": {
								"directory":"20220413-arbitrum-root-gauge-factory"
							},
							"PolygonRootGaugeFactory": {
								"directory":"20220413-polygon-root-gauge-factory"
							},
							"ChildChainStreamer": {
								"directory":"20220413-child-chain-gauge-factory"
							},
							"ChildChainLiquidityGaugeFactory": {
								"directory":"20220413-child-chain-gauge-factory"
							},
							"veBALL2GaugeSetupCoordinator": {
								"directory":"20220415-veBAL-L2-gauge-setup-coordinator"
							},
							"veBALGaugeFixCoordinator": {
								"directory":"20220418-veBAL-gauge-fix-coordinator"
							},
							"FeeDistributor": {
								"directory":"20220420-fee-distributor"
							},
							"SmartWalletChecker": {
								"directory":"20220420-smart-wallet-checker"
							},
							"SmartWalletCheckerCoordinator": {
								"directory":"20220421-smart-wallet-checker-coordinator"
							},
							"DistributionScheduler": {
								"directory":"20220422-distribution-scheduler"
							},
							"ProtocolFeePercentagesProvider": {
								"directory":"20220725-protocol-fee-percentages-provider"
							}
						};

	decimals = {};

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
	def __init__(self, network=None, verbose=True, customConfigFile=None, manualEnv={}):
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
		self.network = network.lower();

		# set high decimal precision
		getcontext().prec = 28;

		# grab parameters from env vars if they exist
		self.infuraApiKey = 		os.environ.get(self.envVarInfura);
		self.customRPC = 			os.environ.get(self.envVarCustomRPC);
		self.etherscanApiKey = 		os.environ.get(self.envVarEtherscan);
		self.privateKey =  			os.environ.get(self.envVarPrivate);

		# override params with manually passed args if they exist
		if "infuraApiKey" in manualEnv.keys():
			self.infuraApiKey = manualEnv["infuraApiKey"];
		if "customRPC" in manualEnv.keys():
			self.customRPC = manualEnv["customRPC"];
		if "etherscanApiKey" in manualEnv.keys():
			self.etherscanApiKey = manualEnv["etherscanApiKey"];
		if "privateKey" in manualEnv.keys():
			self.privateKey = manualEnv["privateKey"];

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

		self.endpoint = endpoint;
		self.web3 = Web3(Web3.HTTPProvider(endpoint));

		acct = self.web3.eth.account.privateKeyToAccount(self.privateKey);
		self.web3.eth.default_account = acct.address;
		self.address = acct.address;

		# initialize gas block caches
		self.currGasPriceSpeed = None;
		self.web3.middleware_onion.add(middleware.time_based_cache_middleware)
		self.web3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
		self.web3.middleware_onion.add(middleware.simple_cache_middleware)

		# add support for PoA chains
		self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)

		if self.verbose:
			print("Initialized account", self.web3.eth.default_account);
			print("Connected to web3 at", endpoint);

		usingCustomConfig = (not customConfigFile is None);
		customConfig = None;
		if usingCustomConfig:

			# load custom config file if it exists, quit if not
			if not os.path.isfile(customConfigFile):
				self.ERROR("Custom config file" + customConfigFile + " not found!");
				quit();
			else:
				with open(customConfigFile,'r') as f:
					customConfig = json.load(f);

			# ensure all required fields are in the customConfig
			requiredFields = ["contracts", "networkParams"]
			hasAllRequirements = True;
			for req in requiredFields:
				if not req in customConfig.keys():
					hasAllRequirements = False;
			if not hasAllRequirements:
				self.ERROR("Not all custom fields are in the custom config!");
				print("You must include:");
				for req in requiredFields:
					print("\t"+req);
				print();
				quit();

			# add network params for network
			currNetworkParams = {
				"id":				customConfig["networkParams"]["id"],
				"blockExplorerUrl":	customConfig["networkParams"]["blockExplorerUrl"]
			}

			if "balFrontend" in customConfig["networkParams"].keys():
				currNetworkParams["balFrontend"] = customConfig["networkParams"]["balFrontend"];
			self.networkParams[self.network] = currNetworkParams;

		self.mc = multicaller.multicaller(	_chainId=self.networkParams[self.network]["id"],
											_web3=self.web3,
											_maxRetries=5,
											_verbose=False,
											_allowFailure=True);

		#reset for the edge case in which we're iterating through multiple networks
		self.deploymentAddresses = {};
		missingContracts = [];
		for contractType in self.contractDirectories.keys():
			subdir = self.contractDirectories[contractType]["directory"];

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
			try:
				if usingCustomConfig:
					currAddress = self.web3.toChecksumAddress(customConfig["contracts"][contractType]);
				else:
					deploymentPath = os.path.join('deployments', subdir, "output", self.network + '.json');
					f = pkgutil.get_data(__name__, deploymentPath).decode();
					currData = json.loads(f);
					currAddress = self.web3.toChecksumAddress(currData[contractType]);
				self.deploymentAddresses[contractType] = currAddress;
			except BaseException as error:
				missingContracts.append(contractType);

		print("Available contracts on", self.network);
		for element in self.deploymentAddresses.keys():
			address = self.deploymentAddresses[element];
			print("\t" + address + "\t" + element);

		print();
		print("Missing contracts on", self.network + ": [" + ", ".join(missingContracts) + "]");

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
			gasPriceGwei = self.getGasPrice(gasSpeed);
		
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
		self.ERROR("Transaction not found in" + str(maxRetries) + "retries.");
		return(False);

	# =====================
	# ====ERC20 methods====
	# =====================
	@cache
	def erc20GetContract(self, tokenAddress):
		# Read files packaged in module
		abiPath = os.path.join('abi/ERC20.json');
		f = pkgutil.get_data(__name__, abiPath).decode();
		abi = json.loads(f);

		token = self.web3.eth.contract(self.web3.toChecksumAddress(tokenAddress), abi=abi)
		return(token);

	@cache
	def erc20GetDecimals(self, tokenAddress):

		# keep the manually maintained cache since the
		# multicaller function can populate it too
		if tokenAddress in self.decimals.keys():
			return(self.decimals[tokenAddress]);

		if tokenAddress == self.ZERO_ADDRESS:
			self.decimals[tokenAddress] = 18;
			return(18);

		token = self.erc20GetContract(tokenAddress);
		decimals = token.functions.decimals().call();
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
			txHash = self.erc20SignAndSendNewAllowance(tokenAddress, allowedAddress, targetAllowance, gasFactor, gasSpeed, nonceOverride=nonceOverride, isAsync=isAsync, gasPriceGweiOverride=gasPriceGweiOverride);
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
	# ======Etherscan======
	# =====================
	def generateEtherscanApiUrl(self):
		etherscanUrl = self.networkParams[self.network]["blockExplorerUrl"]
		separator = ".";
		if self.network in ["kovan", "rinkeby","goerli","optimism"]:
			separator = "-";
		urlFront = "https://api" + separator + etherscanUrl;
		return(urlFront);

	def callEtherscan(self, url, maxRetries=3, verbose=False):
		urlFront = self.generateEtherscanApiUrl();
		url = urlFront + url + self.etherscanApiKey;
		if verbose:
			print("Calling:", url);

		count = 0;
		while count < maxRetries:
			try:
				dt = (time.time() - self.lastEtherscanCallTime);
				if dt < 1.0/self.etherscanMaxRate:
					time.sleep((1.0/self.etherscanMaxRate - dt) * 1.1);

				# faking a user-agent resolves the 403 (forbidden) errors on api-kovan.etherscan.io
				headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","DNT": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"};
				r = requests.get(url, headers=headers);
				if verbose:
					print("\t", r);
				self.lastEtherscanCallTime = time.time();
				data = r.json();
				if verbose:
					print("\t", data);
				return(data);
			except Exception as e:
				print("Exception:", e);
				count += 1;
				delaySec = 2;
				if verbose:
					self.WARN("Etherscan failed " + str(count) + " times. Retrying in " + str(delaySec) + " seconds...");
				time.sleep(delaySec);
		self.ERROR("Etherscan failed " + str(count) + " times.");
		return(False);

	def getGasPriceEtherscanGwei(self, speed, verbose=False):
		if not speed in self.etherscanSpeedDict.keys():
			self.ERROR("Speed entered is:" + speed);
			self.ERROR("Speed must be one of the following options:");
			for s in self.etherscanSpeedDict.keys():
				print("\t" + s);
			return(False);

		urlString = "/api?module=gastracker&action=gasoracle&apikey=";# + self.etherscanApiKey;
		response = self.callEtherscan(urlString, verbose=verbose);
		return(response["result"][self.etherscanSpeedDict[speed]]);

	def getTransactionsByAddress(self, address, internal=False, startblock=0, verbose=False):
		if verbose:
			print("\tQuerying data after block", startblock);

		internalString = "";
		if internal:
			internalString = "internal";

		url = [];
		url.append("/api?module=account&action=txlist{}&address=".format(internalString));
		url.append(address);
		url.append("&startblock={}&endblock=99999999&sort=asc&apikey=".format(startblock));
		urlString = "".join(url);
		txns = self.callEtherscan(urlString, verbose=verbose);

		if int(txns["status"]) == 0:
			self.ERROR("Etherscan query failed. Please try again.");
			return(False);
		elif int(txns["status"]) == 1:
			return(txns["result"]);

	def getTransactionByHash(self, txHash, verbose=False):
		urlString = "/api?module=proxy&action=eth_getTransactionByHash&txhash={}&apikey=".format(txHash);
		txns = self.callEtherscan(urlString, verbose=verbose);

		if verbose:
			print(txns)

		if txns == False:
			return(False);
		return(txns);

	def isContractVerified(self, poolId, verbose=False):
		address = self.balPooldIdToAddress(poolId);
		url = "/api?module=contract&action=getabi&address={}&apikey=".format(address);
		results = self.callEtherscan(url, verbose=verbose);
		if verbose:
			print(results);
		isUnverified = (results["result"] == "Contract source code not verified");
		return(not isUnverified);

	def getGasPricePolygon(self, speed):
		if speed in self.etherscanSpeedDict.keys():
			etherscanGasSpeedNamesToPolygon = {
				"slow":"safeLow",
				"average":"standard",
				"fast":"fast"
			};
			speed = etherscanGasSpeedNamesToPolygon[speed];

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

	def getGasPrice(self, speed):
		allowedSpeeds = list(self.speedDict.keys());
		if speed not in allowedSpeeds:
			self.ERROR("Speed entered is:" + speed);
			self.ERROR("Speed must be one of the following options:");
			for s in allowedSpeeds:
				print("\t" + s);
			return(False);

		if not speed == self.currGasPriceSpeed:
			self.currGasPriceSpeed = speed;
			self.web3.eth.set_gas_price_strategy(self.speedDict[speed]);

		gasPrice = self.web3.eth.generateGasPrice() * 1e-9;
		return(gasPrice)

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
			if rawValue == self.INFINITE or rawValue == self.MAX_UINT_112:
				decimals = 0;
			raw = int(Decimal(rawValue) * Decimal(10**decimals));
			rawTokens.append(raw);
		return(rawTokens);

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
		factory = self.balLoadContract("WeightedPoolFactory");
		(tokens, checksumTokens) = self.balSortTokens(list(poolData["tokens"].keys()));

		intWithDecimalsWeights = [int(Decimal(poolData["tokens"][t]["weight"]) * Decimal(1e18)) for t in tokens];
		swapFeePercentage = int(Decimal(poolData["swapFeePercent"]) * Decimal(1e16));
		rateProviders = [self.web3.toChecksumAddress(poolData["tokens"][token]["rateProvider"]) for token in tokens];

		if not self.balWeightsEqualOne(poolData):
			return(False);

		owner = self.balSetOwner(poolData);

		createFunction = factory.functions.create(	poolData["name"], 
													poolData["symbol"], 
													checksumTokens, 
													intWithDecimalsWeights,
													rateProviders,
													swapFeePercentage, 
													owner);
		return(createFunction);

	def balCreateFnWeightedPool2TokensFactory(self, poolData):
		factory = self.balLoadContract("WeightedPool2TokensFactory");
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
		factory = self.balLoadContract("StablePoolFactory");
		(tokens, checksumTokens) = self.balSortTokens(list(poolData["tokens"].keys()));
		swapFeePercentage = int(Decimal(poolData["swapFeePercent"]) * Decimal(1e16));

		owner = self.balSetOwner(poolData);

		createFunction = factory.functions.create(	poolData["name"],
													poolData["symbol"],
													checksumTokens,
													int(poolData["amplificationParameter"]),
													swapFeePercentage,
													owner);
		return(createFunction);


	def balCreateFnLBPoolFactory(self, poolData):
		return(self.balCreateFnLBPFactory(poolData, "LiquidityBootstrappingPoolFactory"));

	def balCreateFnNoProtocolFeeLiquidityBootstrappingPoolFactory(self, poolData):
		return(self.balCreateFnLBPFactory(poolData, "NoProtocolFeeLiquidityBootstrappingPoolFactory"));

	def balCreateFnLBPFactory(self, poolData, factoryName):
		factory = self.balLoadContract(factoryName);
		(tokens, checksumTokens) = self.balSortTokens(list(poolData["tokens"].keys()));

		if not self.balWeightsEqualOne(poolData):
			return(False);

		swapFeePercentage = int(Decimal(poolData["swapFeePercent"]) * Decimal(1e16));
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
		factory = self.balLoadContract("MetaStablePoolFactory");
		(tokens, checksumTokens) = self.balSortTokens(list(poolData["tokens"].keys()));
		swapFeePercentage = int(Decimal(poolData["swapFeePercent"]) * Decimal(1e16));
		owner = self.balSetOwner(poolData);

		rateProviders = [self.web3.toChecksumAddress(poolData["tokens"][token]["rateProvider"]) for token in tokens]
		priceRateCacheDurations = [int(poolData["tokens"][token]["priceRateCacheDuration"]) for token in tokens]

		createFunction = factory.functions.create(	poolData["name"],
													poolData["symbol"],
													checksumTokens,
													int(poolData["amplificationParameter"]),
													rateProviders,
													priceRateCacheDurations,
													swapFeePercentage,
													poolData["oracleEnabled"],
													owner);
		return(createFunction);

	def balCreateFnInvestmentPoolFactory(self, poolData):
		factory = self.balLoadContract("InvestmentPoolFactory");
		(tokens, checksumTokens) = self.balSortTokens(list(poolData["tokens"].keys()));
		swapFeePercentage = int(Decimal(poolData["swapFeePercent"]) * Decimal(1e16));
		intWithDecimalsWeights = [int(Decimal(poolData["tokens"][t]["weight"]) * Decimal(1e18)) for t in tokens];
		managementFeePercentage = int(Decimal(poolData["managementFeePercent"]) * Decimal(1e16));
		# Deployed factory doesn't allow asset managers
		# assetManagers = [0 for i in range(0,len(tokens))]
		owner = self.balSetOwner(poolData);
		if not owner == self.address:
			self.WARN("!!! You are not the owner for your Investment Pool !!!")
			self.WARN("You:\t\t" + self.address)
			self.WARN("Pool Owner:\t" + owner)

			print();
			self.WARN("Only the pool owner can call permissioned functions, such as changing weights or the management fee.")
			self.WARN(owner + " should either be you, or a multi-sig or other contract that you control and can call permissioned functions from.")
			cancelTimeSec = 30;
			self.WARN("If the owner mismatch is was unintentional, you have " + str(cancelTimeSec) + " seconds to cancel with Ctrl+C.")
			time.sleep(cancelTimeSec);

		createFunction = factory.functions.create(	poolData["name"],
													poolData["symbol"],
													checksumTokens,
													intWithDecimalsWeights,
													swapFeePercentage,
													owner,
													poolData["swapEnabledOnStart"],
													managementFeePercentage);
		return(createFunction);

	def balCreateFnManagedPoolFactory(self, poolData):
		self.WARN("!!! You are using the Managed Pool Factory without a controller !!!")
		self.WARN("You are currently using a factory to deploy a managed pool without a factory-provided controller contract.")
		self.WARN("It is highly recommended that you use a factory that pairs a controller with a pool")
		self.WARN("While this will be a valid pool, the owner will have a dangerous level of power over the pool")
		self.WARN("It *is* technically possible to add a controller contract as `owner`, but using a factory-paired one provides more guarantees")

		factory = self.balLoadContract("ManagedPoolFactory");
		(tokens, checksumTokens) = self.balSortTokens(list(poolData["tokens"].keys()));
		swapFeePercentage = int(Decimal(poolData["swapFeePercent"]) * Decimal(1e16));
		intWithDecimalsWeights = [int(Decimal(poolData["tokens"][t]["weight"]) * Decimal(1e18)) for t in tokens];
		assetManagers = [poolData["tokens"][t]["assetManager"] for t in tokens];
		managementAumFeePercentage = int(Decimal(poolData["managementAumFeePercentage"]) * Decimal(1e16));

		owner = self.balSetOwner(poolData);
		if not owner == self.address:
			self.WARN("!!! You are not the owner for your Managed Pool !!!")
			self.WARN("You:\t\t" + self.address)
			self.WARN("Pool Owner:\t" + owner)

			print();
			self.WARN("Only the pool owner can call permissioned functions, such as changing weights or the management fee.")
			self.WARN(owner + " should either be you, or a multi-sig or other contract that you control and can call permissioned functions from.")
			cancelTimeSec = 30;
			self.WARN("If the owner mismatch is was unintentional, you have " + str(cancelTimeSec) + " seconds to cancel with Ctrl+C.")
			time.sleep(cancelTimeSec);

		createFunction = factory.functions.create(
			(
				poolData["name"],
				poolData["symbol"],
				checksumTokens,
				intWithDecimalsWeights,
				assetManagers,
				swapFeePercentage,
				poolData["swapEnabledOnStart"],
				poolData["mustAllowlistLPs"],
				managementAumFeePercentage,
				int(poolData["aumFeeId"])
			),
			owner
		);
		return(createFunction);

	def balCreateFnStablePhantomPoolFactory(self, poolData):
		factory = self.balLoadContract("StablePhantomPoolFactory");
		(tokens, checksumTokens) = self.balSortTokens(list(poolData["tokens"].keys()));
		swapFeePercentage = int(Decimal(poolData["swapFeePercent"]) * Decimal(1e16));
		owner = self.balSetOwner(poolData);

		rateProviders = [self.web3.toChecksumAddress(poolData["tokens"][token]["rateProvider"]) for token in tokens]
		tokenRateCacheDurations = [int(poolData["tokens"][token]["tokenRateCacheDuration"]) for token in tokens]

		createFunction = factory.functions.create(	poolData["name"],
													poolData["symbol"],
													checksumTokens,
													int(poolData["amplificationParameter"]),
													rateProviders,
													tokenRateCacheDurations,
													swapFeePercentage,
													owner);
		return(createFunction);

	def balCreateFnComposableStablePoolFactory(self, poolData):
		factory = self.balLoadContract("ComposableStablePoolFactory");
		(tokens, checksumTokens) = self.balSortTokens(list(poolData["tokens"].keys()));
		swapFeePercentage = int(Decimal(poolData["swapFeePercent"]) * Decimal(1e16));
		owner = self.balSetOwner(poolData);

		rateProviders = [self.web3.toChecksumAddress(poolData["tokens"][token]["rateProvider"]) for token in tokens]
		tokenRateCacheDurations = [int(poolData["tokens"][token]["tokenRateCacheDuration"]) for token in tokens]
		exemptFromYieldProtocolFeeFlags = [bool(poolData["tokens"][token]["exemptFromYieldProtocolFeeFlags"]) for token in tokens]

		createFunction = factory.functions.create(	poolData["name"],
													poolData["symbol"],
													checksumTokens,
													int(poolData["amplificationParameter"]),
													rateProviders,
													tokenRateCacheDurations,
													exemptFromYieldProtocolFeeFlags,
													swapFeePercentage,
													owner);
		return(createFunction);

	def balCreateFnLinearPoolFactory(self, poolData, factoryName):
		factory = self.balLoadContract(factoryName);
		(tokens, checksumTokens) = self.balSortTokens(list(poolData["tokens"].keys()));
		swapFeePercentage = int(Decimal(poolData["swapFeePercent"]) * Decimal(1e16));
		owner = self.balSetOwner(poolData);

		mainToken = None;
		wrappedToken = None;
		for token in poolData["tokens"].keys():
			if poolData["tokens"][token]["isWrappedToken"]:
				wrappedToken = token;
			else:
				mainToken = token;

		if mainToken == wrappedToken:
			self.ERROR("AaveLinearPool must have one wrappedToken and one mainToken. Please check your inputs. Quitting...");
			return(False);

		upperTarget = int(poolData["upperTarget"]);
		createFunction = factory.functions.create(	poolData["name"],
													poolData["symbol"],
													self.web3.toChecksumAddress(mainToken),
													self.web3.toChecksumAddress(wrappedToken),
													upperTarget,
													swapFeePercentage,
													owner);
		return(createFunction);

	def balCreateFnAaveLinearPoolFactory(self, poolData):
		return(self.balCreateFnLinearPoolFactory(poolData, "AaveLinearPoolFactory"));

	def balCreateFnERC4626LinearPoolFactory(self, poolData):
		return(self.balCreateFnLinearPoolFactory(poolData, "ERC4626LinearPoolFactory"));

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
		if poolFactoryName == "InvestmentPoolFactory":
			createFunction = self.balCreateFnInvestmentPoolFactory(poolDescription);
		if poolFactoryName == "ManagedPoolFactory":
			createFunction = self.balCreateFnManagedPoolFactory(poolDescription);
		if poolFactoryName == "StablePhantomPoolFactory":
			createFunction = self.balCreateFnStablePhantomPoolFactory(poolDescription);
		if poolFactoryName == "ComposableStablePoolFactory":
			createFunction = self.balCreateFnComposableStablePoolFactory(poolDescription);
		if poolFactoryName == "AaveLinearPoolFactory":
			createFunction = self.balCreateFnAaveLinearPoolFactory(poolDescription);
		if poolFactoryName == "ERC4626LinearPoolFactory":
			createFunction = self.balCreateFnERC4626LinearPoolFactory(poolDescription);
		if poolFactoryName == "NoProtocolFeeLiquidityBootstrappingPoolFactory":
			createFunction = self.balCreateFnNoProtocolFeeLiquidityBootstrappingPoolFactory(poolDescription);
		if createFunction is None:
			print("No pool factory found with name:", poolFactoryName);
			print("Currently supported pool types are:");
			print("\tWeightedPool");
			print("\tWeightedPool2Token");
			print("\tStablePool");
			print("\tLiquidityBootstrappingPool");
			print("\tMetaStablePool");
			print("\tInvestmentPool");
			print("\tStablePhantomPool");
			print("\tComposableStablePoolFactory");
			print("\tAaveLinearPool");
			print("\tERC4626LinearPoolFactory");
			print("\tNoProtocolFeeLiquidityBootstrappingPoolFactory");
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
		vault = self.balLoadContract("Vault");

		with Suppressor():
			logs = vault.events.PoolRegistered().processReceipt(receipt);
			poolId = logs[0]['args']['poolId'].hex();

		print("Your pool ID is:");
		print("\t0x" + str(poolId));
		return(poolId);

	def balFindPoolFactory(self, poolId):
		contractNames = self.deploymentAddresses.keys();
		factoryNames = [c for c in contractNames if ("Factory" in c) and ("Pool" in c)]; #can't simply use "PoolFactory" b/c of WeightedPool2TokensFactory

		self.mc.reset();
		for factoryName in factoryNames:
			factory = self.balLoadContract(factoryName);
			poolAddress = self.balPooldIdToAddress(poolId);
			self.mc.addCall(factory.address, factory.abi, "isPoolFromFactory", args=[poolAddress]);
		(data, successes) = self.mc.execute();

		foundFactoryName = None;
		numFound = 0;
		for f,d in zip(factoryNames, data):
			if d[0]:
				foundFactoryName = f;
				numFound += 1;

		if numFound == 1:
			return(foundFactoryName);
		else:
			self.ERROR("Was expecting 1 factory, got " + str(numFound));
			self.ERROR("Checked the following factories:\n\t\t" + "\n\t\t".join(factoryNames));
			return(None);

	def balGetJoinKindEnum(self, poolId, joinKind):
		factoryName = self.balFindPoolFactory(poolId);

		usingWeighted = factoryName in ["WeightedPoolFactory", "WeightedPool2TokensFactory", "LiquidityBootstrappingPoolFactory", "InvestmentPoolFactory", "NoProtocolFeeLiquidityBootstrappingPoolFactory", "ManagedPoolFactory"];
		usingStable = factoryName in ["StablePoolFactory", "MetaStablePoolFactory"];
		usingStablePhantom = factoryName in ["StablePhantomPoolFactory", "ComposableStablePoolFactory"];

		if usingWeighted:
			joinKindEnum = WeightedPoolJoinKind[joinKind];
		elif usingStable:
			joinKindEnum = StablePoolJoinKind[joinKind];
		elif usingStablePhantom:
			joinKindEnum = StablePhantomPoolJoinKind[joinKind];
		else:
			self.ERROR("PoolType " + str(factoryName) + " not supported for JoinKind: " + joinKind)
			return(None);
		return(joinKindEnum);

	def balGetTokensAndAmounts(self, joinDescription):
		(sortedTokens, checksumTokens) = self.balSortTokens(list(joinDescription["tokens"].keys()));
		amountKey = "amount";
		if not amountKey in joinDescription["tokens"][list(joinDescription["tokens"].keys())[0]].keys():
			amountKey = "initialBalance";
		amountsBySortedTokens = [joinDescription["tokens"][token][amountKey] for token in sortedTokens];
		maxAmountsIn = self.balConvertTokensToWei(sortedTokens, amountsBySortedTokens);
		return(checksumTokens, maxAmountsIn);

	def balGetTokensAndAmountsComposable(self, joinDescription):
		(checksumTokens, maxAmountsIn) = self.balGetTokensAndAmounts(joinDescription);

		poolAddress = self.balPooldIdToAddress(joinDescription["poolId"]);
		poolAddress = self.web3.toChecksumAddress(poolAddress);

		composableAmount = None;

		userDataMaxAmountIn = copy.deepcopy(maxAmountsIn);

		for i in range(len(checksumTokens)):
			if checksumTokens[i] == poolAddress:
				composableAmount = maxAmountsIn[i];
				del checksumTokens[i];
				del maxAmountsIn[i];
				del userDataMaxAmountIn[i];
				break;

		checksumTokens.insert(0, poolAddress);
		maxAmountsIn.insert(0, composableAmount);

		return(checksumTokens, maxAmountsIn, userDataMaxAmountIn);

	def balDoJoinPool(self, poolId, address, joinPoolRequestTuple, gasFactor=1.05, gasPriceSpeed="average", nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):
		vault = self.balLoadContract("Vault");
		joinPoolFunction = vault.functions.joinPool(poolId, address, address, joinPoolRequestTuple);
		tx = self.buildTx(joinPoolFunction, gasFactor, gasPriceSpeed, nonceOverride, gasEstimateOverride, gasPriceGweiOverride);
		print("Transaction Generated!");
		txHash = self.sendTx(tx);
		return(txHash);

	def balDoQueryJoinPool(self, poolId, address, joinPoolRequestTuple):
		bh = self.balLoadContract("BalancerHelpers");
		(bptOut, amountsIn) = bh.functions.queryJoin(poolId, address, address, joinPoolRequestTuple).call();
		return((bptOut, amountsIn));

	def balFormatJoinPoolInit(self, joinDescription):
		(checksumTokens, maxAmountsIn) = self.balGetTokensAndAmounts(copy.deepcopy(joinDescription));

		poolId = joinDescription["poolId"];
		factory = self.balFindPoolFactory(poolId);

		userDataMaxAmountsIn = maxAmountsIn;
		if factory in ["ManagedPoolFactory"]:
			(checksumTokens, maxAmountsIn, userDataMaxAmountsIn) = self.balGetTokensAndAmountsComposable(copy.deepcopy(joinDescription));

		joinKindEnum = self.balGetJoinKindEnum(poolId, joinDescription["joinKind"]);
		userDataEncoded = eth_abi.encode_abi(	['uint256', 'uint256[]'],
												[int(joinKindEnum), userDataMaxAmountsIn]);
		address = self.web3.toChecksumAddress(self.web3.eth.default_account);
		joinPoolRequestTuple = (checksumTokens, maxAmountsIn, userDataEncoded.hex(), joinDescription["fromInternalBalance"]);
		return(poolId, address, joinPoolRequestTuple);

	def balFormatJoinPoolExactTokensInForBptOut(self, joinDescription):
		(checksumTokens, maxAmountsIn) = self.balGetTokensAndAmounts(copy.deepcopy(joinDescription));
		poolId = joinDescription["poolId"];
		joinKindEnum = self.balGetJoinKindEnum(poolId, joinDescription["joinKind"]);
		userDataEncoded = eth_abi.encode_abi(	['uint256', 'uint256[]'],
												[int(joinKindEnum), maxAmountsIn]);
		address = self.web3.toChecksumAddress(self.web3.eth.default_account);
		joinPoolRequestTuple = (checksumTokens, maxAmountsIn, userDataEncoded.hex(), joinDescription["fromInternalBalance"]);
		return(poolId, address, joinPoolRequestTuple);

	def balFormatJoinPoolAllTokensInForExactBptOut(self, joinDescription):
		(checksumTokens, maxAmountsIn) = self.balGetTokensAndAmounts(copy.deepcopy(joinDescription));
		poolId = joinDescription["poolId"];
		poolAddress = self.balPooldIdToAddress(poolId);
		bptAmountOut = self.balConvertTokensToWei([poolAddress], [joinDescription["bptAmountOut"]])[0];

		joinKindEnum = self.balGetJoinKindEnum(poolId, joinDescription["joinKind"]);
		userDataEncoded = eth_abi.encode_abi(	['uint256', 'uint256'],
												[int(joinKindEnum), bptAmountOut]);
		address = self.web3.toChecksumAddress(self.web3.eth.default_account);
		joinPoolRequestTuple = (checksumTokens, maxAmountsIn, userDataEncoded.hex(), joinDescription["fromInternalBalance"]);
		return(poolId, address, joinPoolRequestTuple);

	def balFormatJoinPoolTokenInForExactBptOut(self, joinDescription):
		(checksumTokens, maxAmountsIn) = self.balGetTokensAndAmounts(copy.deepcopy(joinDescription));

		index = -1;
		counter = -1;
		for amt in maxAmountsIn:
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

		poolId = joinDescription["poolId"];
		poolAddress = self.balPooldIdToAddress(poolId);
		bptAmountOut = self.balConvertTokensToWei([poolAddress], [joinDescription["bptAmountOut"]])[0];

		joinKindEnum = self.balGetJoinKindEnum(poolId, joinDescription["joinKind"]);
		userDataEncoded = eth_abi.encode_abi(	['uint256', 'uint256', 'uint256'],
												[int(joinKindEnum), bptAmountOut, index]);

		address = self.web3.toChecksumAddress(self.web3.eth.default_account);
		joinPoolRequestTuple = (checksumTokens, maxAmountsIn, userDataEncoded.hex(), joinDescription["fromInternalBalance"]);

		return(poolId, address, joinPoolRequestTuple);

	def balJoinPool(self, joinDescription, query=False, gasFactor=1.05, gasPriceSpeed="average", nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):
		joinKind = joinDescription["joinKind"];
		poolId = None;
		address = None;
		joinPoolRequestTuple = None;

		if joinKind == "INIT":
			(poolId, address, joinPoolRequestTuple) = self.balFormatJoinPoolInit(joinDescription);
		elif joinKind == "EXACT_TOKENS_IN_FOR_BPT_OUT":
			(poolId, address, joinPoolRequestTuple) = self.balFormatJoinPoolExactTokensInForBptOut(joinDescription);
		elif joinKind == "TOKEN_IN_FOR_EXACT_BPT_OUT":
			tempJoinDescription = copy.deepcopy(joinDescription);
			if query:
				for token in tempJoinDescription["tokens"].keys():
					if tempJoinDescription["tokens"][token]["amount"] == 0.0:
						tempJoinDescription["tokens"][token]["amount"] = self.INFINITE;
			(poolId, address, joinPoolRequestTuple) = self.balFormatJoinPoolTokenInForExactBptOut(tempJoinDescription);
		elif joinKind == "ALL_TOKENS_IN_FOR_EXACT_BPT_OUT":
			tempJoinDescription = copy.deepcopy(joinDescription);
			if query:
				for token in tempJoinDescription["tokens"].keys():
					tempJoinDescription["tokens"][token]["amount"] = self.INFINITE;
			(poolId, address, joinPoolRequestTuple) = self.balFormatJoinPoolAllTokensInForExactBptOut(tempJoinDescription);
			print((poolId, address, joinPoolRequestTuple))

		if query:
			(bptOut, amountsIn) = self.balDoQueryJoinPool(poolId, address, joinPoolRequestTuple);
			bptAddress = self.balPooldIdToAddress(poolId);
			outputData = {};
			outputData["bptOut"] = {
				"token":bptAddress,
				"decimals":self.erc20GetDecimals(bptAddress),
				"amount":bptOut
			}
			outputData["amountsIn"] = {};
			for token, amount in zip(joinPoolRequestTuple[0], amountsIn):
				outputData["amountsIn"][token] = {
					"token":token,
					"decimals":self.erc20GetDecimals(token),
					"amount":amount
				}
			return(outputData);
		else:
			txHash = self.balDoJoinPool(poolId, address, joinPoolRequestTuple, gasFactor=gasFactor, gasPriceSpeed=gasPriceSpeed, nonceOverride=nonceOverride, gasEstimateOverride=gasEstimateOverride, gasPriceGweiOverride=gasPriceGweiOverride);
			return(txHash);

	def balRegisterPoolWithVault(self, poolDescription, poolId, gasFactor=1.05, gasPriceSpeed="average", nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):
		self.WARN("\"balRegisterPoolWithVault\" is deprecated. Please use \"balJoinPoolInit\".")
		self.balJoinPoolInit(poolDescription, poolId, gasFactor, gasPriceSpeed, nonceOverride, gasEstimateOverride, gasPriceGweiOverride)

	def balJoinPoolInit(self, poolDescription, poolId, gasFactor=1.05, gasPriceSpeed="average", nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):

		if poolDescription["poolType"] in ["AaveLinearPool"]:
			slippageTolerancePercent = 1;
			txHash = self.balLinearPoolInitJoin(poolDescription, poolId, slippageTolerancePercent=slippageTolerancePercent, gasFactor=gasFactor, gasPriceSpeed=gasPriceSpeed, nonceOverride=nonceOverride, gasEstimateOverride=gasEstimateOverride, gasPriceGweiOverride=gasPriceGweiOverride);
			return(txHash)

		# StablePhantomPools need their own BPT as one of the provided tokens with a limit of MAX_UINT_112
		if poolDescription["poolType"] in ["StablePhantomPool", "ComposableStablePool", "ManagedPool"]:
			initialBalancesNoBpt = [poolDescription["tokens"][token]["initialBalance"] for token in poolDescription["tokens"].keys()];
			phantomBptAddress = self.balPooldIdToAddress(poolId);
			poolDescription["tokens"][phantomBptAddress] = {"initialBalance":self.MAX_UINT_112}

		poolDescription["joinKind"] = "INIT";
		return(self.balJoinPool(poolDescription, False, gasFactor, gasPriceSpeed, nonceOverride, gasEstimateOverride, gasPriceGweiOverride));

	def balLinearPoolInitJoin(self, poolDescription, poolId, slippageTolerancePercent=1, gasFactor=1.05, gasPriceSpeed="average", nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):

		phantomBptAddress = self.balPooldIdToAddress(poolId);

		batchSwap = {};
		batchSwap["kind"] = 0;
		batchSwap["assets"] = list(poolDescription["tokens"].keys());
		batchSwap["swaps"] = [];

		numTokens = len(batchSwap["assets"]);
		for i in range(numTokens):
			token = batchSwap["assets"][i];
			swap = {};
			swap["poolId"] = "0x" + poolId;
			swap["assetInIndex"] = i;
			swap["assetOutIndex"] = numTokens;
			swap["amount"] = poolDescription["tokens"][token]["initialBalance"];
			if float(swap["amount"]) > 0.0:
				batchSwap["swaps"].append(swap);

		# add the phantomBpt to the assets/limits list now that we've crafted the swap steps
		batchSwap["assets"].append(phantomBptAddress);
		batchSwap["limits"] = [0] * len(batchSwap["assets"]); #for now

		batchSwap["funds"] = {};
		batchSwap["funds"]["sender"] = self.address;
		batchSwap["funds"]["recipient"] = self.address;
		batchSwap["funds"]["fromInternalBalance"] = False;
		batchSwap["funds"]["toInternalBalance"] = False;
		batchSwap["deadline"] = "999999999999999999";

		estimates = self.balQueryBatchSwap(batchSwap);

		checksumTokens = [self.web3.toChecksumAddress(t) for t in batchSwap["assets"]];
		for i in range(len(batchSwap["assets"])):
			asset = checksumTokens[i];
			slippageToleranceFactor = slippageTolerancePercent/100.0;
			if estimates[asset] < 0:
				slippageToleranceFactor *= -1.0;
			batchSwap["limits"][i] = estimates[asset] * (1.0 + slippageToleranceFactor);

		txHash = self.balDoBatchSwap(batchSwap, isAsync=False, gasFactor=gasFactor, gasPriceSpeed=gasPriceSpeed, nonceOverride=nonceOverride, gasEstimateOverride=gasEstimateOverride, gasPriceGweiOverride=gasPriceGweiOverride);
		return(txHash)

	def balVaultWeth(self):
		vault = self.balLoadContract("Vault");
		wethAddress = vault.functions.WETH().call();
		return(wethAddress);

	def balBalancerHelpersGetVault(self):
		bh = self.balLoadContract("BalancerHelpers");
		vaultAddress = bh.functions.vault().call();
		return(vaultAddress);

	def balVaultGetPoolTokens(self, poolId):
		vault = self.balLoadContract("Vault");
		output = vault.functions.getPoolTokens(poolId).call();
		tokens = output[0];
		balances = output[1];
		lastChangeBlock = output[2];
		return (tokens, balances, lastChangeBlock);

	def balVaultGetInternalBalance(self, tokens, address=None):
		if address is None:
			address = self.web3.eth.default_account;

		vault = self.balLoadContract("Vault");
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

		vault = self.balLoadContract("Vault");
		manageUserBalanceFn = vault.functions.manageUserBalance(inputTupleList);
		return(manageUserBalanceFn);

	@cache
	def balLoadContract(self, contractName):
		contract = self.web3.eth.contract(address=self.deploymentAddresses[contractName], abi=self.abis[contractName]);
		return(contract)

	@cache
	def balLoadArbitraryContract(self, address, abi):
		contract = self.web3.eth.contract(address=address, abi=self.mc.stringToList(abi));
		return(contract);

	@cache
	def balPoolGetAbi(self, poolType):

		if not "Pool" in poolType:
			poolType = poolType + "Pool"

		deploymentFolder = self.contractDirectories[poolType + "Factory"]["directory"];
		abiPath = os.path.join("deployments/", deploymentFolder, "abi", poolType + ".json");
		f = pkgutil.get_data(__name__, abiPath).decode();
		poolAbi = json.loads(f);
		return(poolAbi);

	@cache
	def balPooldIdToAddress(self, poolId):
		if not "0x" in poolId:
			poolId = "0x" + poolId;
		poolAddress = self.web3.toChecksumAddress(poolId[:42]);
		return(poolAddress);

	def balGetPoolCreationData(self, poolId, verbose=False, inputHash=None):
		address = self.balPooldIdToAddress(poolId);
		if inputHash is None:
			txns = self.getTransactionsByAddress(address, internal=True, verbose=verbose);
		else:
			txns = self.getTransactionByHash(inputHash, verbose=verbose);

		poolTypeByContract = {};
		for poolType in self.deploymentAddresses.keys():
			deploymentAddress = self.deploymentAddresses[poolType].lower();
			poolTypeByContract[deploymentAddress] = poolType;

		poolFactoryType = None;
		if inputHash is None:
			for txn in txns:
				if txn["from"].lower() in poolTypeByContract.keys():
					poolFactoryType = poolTypeByContract[txn["from"].lower()];
					txHash = txn["hash"];
					stamp = txn["timeStamp"];
					break;
		else:
			txn = txns["result"];
			if verbose:
				print();
				print(txn);
			poolFactoryType = poolTypeByContract[txn["to"].lower()];
			txHash = txn["hash"];
			stamp = self.web3.eth.get_block(int(txn["blockNumber"],16))["timestamp"];

		return(address, poolFactoryType, txHash, stamp);

	def balGetPoolFactoryCreationTime(self, address):
		txns = self.getTransactionsByAddress(address);
		return(txns[0]["timeStamp"]);

	def getInputData(self, txHash):
		transaction = self.web3.eth.get_transaction(txHash);
		return(transaction.input)

	def balGeneratePoolCreationArguments(self, poolId, verbose=False, creationHash=None):
		if self.network in ["arbitrum"]:
			self.ERROR("Automated pool verification doesn't work on " + self.network + " yet. Please try the method outlined in the docs using Tenderly.");
			return(False);

		# query etherscan for internal transactions to find pool factory, pool creation time, and creation hash
		(address, poolFactoryType, txHash, stampPool) = self.balGetPoolCreationData(poolId, verbose=verbose, inputHash=creationHash);

		# get the input data used to generate the pool
		inputData = self.getInputData(txHash);

		# decode those ^ inputs according to the relevant pool factory ABI
		poolFactoryContract = self.balLoadContract(poolFactoryType)
		decodedPoolData = poolFactoryContract.decode_function_input(inputData)[1];

		# get pool factory creation time to calculate pauseWindowDuration
		stampFactory = self.balGetPoolFactoryCreationTime(poolFactoryContract.address);

		# make sure arguments exist/are proper types to be encoded
		if "weights" in decodedPoolData.keys():
			for i in range(len(decodedPoolData["weights"])):
				decodedPoolData["weights"][i] = int(decodedPoolData["weights"][i]);
		if "priceRateCacheDuration" in decodedPoolData.keys():
			for i in range(len(decodedPoolData["priceRateCacheDuration"])):
				decodedPoolData["priceRateCacheDuration"][i] = int(decodedPoolData["priceRateCacheDuration"][i]);
		if poolFactoryType == "InvestmentPoolFactory" and not "assetManagers" in decodedPoolData.keys():
			decodedPoolData["assetManagers"] = [];
			for i in range(len(decodedPoolData["weights"])):
				decodedPoolData["assetManagers"].append(self.ZERO_ADDRESS);

		# times for pause/buffer
		daysToSec = 24*60*60; # hr * min * sec
		pauseDays = 90;
		bufferPeriodDays = 30;

		# calculate proper durations
		pauseWindowDurationSec = max( (pauseDays*daysToSec) - (int(stampPool) - int(stampFactory)), 0);
		bufferPeriodDurationSec = bufferPeriodDays * daysToSec;
		if pauseWindowDurationSec == 0:
			bufferPeriodDurationSec = 0;

		poolType = poolFactoryType.replace("Factory","");
		poolAbi = self.balPoolGetAbi(poolType);

		structInConstructor = False;
		if poolType == "WeightedPool":
			zero_ams = [self.ZERO_ADDRESS] * len(decodedPoolData["tokens"]);
			args = [(decodedPoolData["name"],
					decodedPoolData["symbol"],
					decodedPoolData["tokens"],
					decodedPoolData["normalizedWeights"],
					decodedPoolData["rateProviders"],
					zero_ams,
					int(decodedPoolData["swapFeePercentage"])),
					self.deploymentAddresses["Vault"],
					self.deploymentAddresses["ProtocolFeePercentagesProvider"],
					int(pauseWindowDurationSec),
					int(bufferPeriodDurationSec),
					decodedPoolData["owner"]];
		elif poolType == "WeightedPool2Tokens":
			args = [self.deploymentAddresses["Vault"],
					decodedPoolData["name"],
					decodedPoolData["symbol"],
					decodedPoolData["tokens"][0],
					decodedPoolData["tokens"][1],
					int(decodedPoolData["weights"][0]),
					int(decodedPoolData["weights"][1]),
					int(decodedPoolData["swapFeePercentage"]),
					int(pauseWindowDurationSec),
					int(bufferPeriodDurationSec),
					decodedPoolData["oracleEnabled"],
					decodedPoolData["owner"]];
			structInConstructor = True;
		elif poolType == "StablePool":
			args = [self.deploymentAddresses["Vault"],
					decodedPoolData["name"],
					decodedPoolData["symbol"],
					decodedPoolData["tokens"],
					int(decodedPoolData["amplificationParameter"]),
					int(decodedPoolData["swapFeePercentage"]),
					int(pauseWindowDurationSec),
					int(bufferPeriodDurationSec),
					decodedPoolData["owner"]];
		elif poolType == "MetaStablePool":
			args = [self.deploymentAddresses["Vault"],
					decodedPoolData["name"],
					decodedPoolData["symbol"],
					decodedPoolData["tokens"],
					decodedPoolData["rateProviders"],
					decodedPoolData["priceRateCacheDuration"],
					int(decodedPoolData["amplificationParameter"]),
					int(decodedPoolData["swapFeePercentage"]),
					int(pauseWindowDurationSec),
					int(bufferPeriodDurationSec),
					decodedPoolData["oracleEnabled"],
					decodedPoolData["owner"]];
			structInConstructor = True;
		elif poolType == "LiquidityBootstrappingPool":
			args = [self.deploymentAddresses["Vault"],
					decodedPoolData["name"],
					decodedPoolData["symbol"],
					decodedPoolData["tokens"],
					decodedPoolData["weights"],
					int(decodedPoolData["swapFeePercentage"]),
					int(pauseWindowDurationSec),
					int(bufferPeriodDurationSec),
					decodedPoolData["owner"],
					decodedPoolData["swapEnabledOnStart"]];
		elif poolType == "InvestmentPool":
			args = [self.deploymentAddresses["Vault"],
					decodedPoolData["name"],
					decodedPoolData["symbol"],
					decodedPoolData["tokens"],
					decodedPoolData["weights"],
					decodedPoolData["assetManagers"],
					int(decodedPoolData["swapFeePercentage"]),
					int(pauseWindowDurationSec),
					int(bufferPeriodDurationSec),
					decodedPoolData["owner"],
					decodedPoolData["swapEnabledOnStart"],
					int(decodedPoolData["managementSwapFeePercentage"])];
			structInConstructor = True;
		elif poolType == "StablePhantomPool":
			args = [self.deploymentAddresses["Vault"],
				decodedPoolData["name"],
				decodedPoolData["symbol"],
				decodedPoolData["tokens"],
				decodedPoolData["rateProviders"],
				decodedPoolData["tokenRateCacheDurations"],
				int(decodedPoolData["amplificationParameter"]),
				int(decodedPoolData["swapFeePercentage"]),
				int(pauseWindowDurationSec),
				int(bufferPeriodDurationSec),
				decodedPoolData["owner"]];
			structInConstructor = True;
		elif poolType == "AaveLinearPool":
			args = [self.deploymentAddresses["Vault"],
				decodedPoolData["name"],
				decodedPoolData["symbol"],
				decodedPoolData["mainToken"],
				decodedPoolData["wrappedToken"],
				int(decodedPoolData["upperTarget"]),
				int(decodedPoolData["swapFeePercentage"]),
				int(pauseWindowDurationSec),
				int(bufferPeriodDurationSec),
				decodedPoolData["owner"]];
		elif poolType == "ERC4626LinearPool":
			args = [self.deploymentAddresses["Vault"],
				decodedPoolData["name"],
				decodedPoolData["symbol"],
				decodedPoolData["mainToken"],
				decodedPoolData["wrappedToken"],
				int(decodedPoolData["upperTarget"]),
				int(decodedPoolData["swapFeePercentage"]),
				int(pauseWindowDurationSec),
				int(bufferPeriodDurationSec),
				decodedPoolData["owner"]];
		else:
			self.ERROR("PoolType " + poolType + " not found!")
			return(False);

		# encode constructor data
		poolContract = self.balLoadArbitraryContract(address, self.mc.listToString(poolAbi));
		if structInConstructor:
			args = (tuple(args),)
		data = poolContract._encode_constructor_data(args=args);
		encodedData = data[2:]; #cut off the 0x

		command = "yarn hardhat verify-contract --id {} --name {} --address {} --network {} --key {} --args {}"
		output = command.format(self.contractDirectories[poolFactoryType]["directory"],
								poolType,
								address,
								self.network,
								self.etherscanApiKey,
								encodedData)
		return(output);

	def balStablePoolGetAmplificationParameter(self, poolId):
		poolAddress = self.web3.toChecksumAddress(poolId[:42]);
		pool = self.web3.eth.contract(address=poolAddress, abi=self.balPoolGetAbi("StablePool"));
		(value, isUpdating, precision) = pool.functions.getAmplificationParameter().call();
		return(value, isUpdating, precision); 
	
	def balStablePoolStartAmplificationParameterUpdate(self, poolId, rawEndValue, endTime, isAsync=False, gasFactor=1.05, gasPriceSpeed="average", nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):
		poolAddress = self.web3.toChecksumAddress(poolId[:42]);
		pool = self.web3.eth.contract(address=poolAddress, abi=self.balPoolGetAbi("StablePool"));
		 
		owner = pool.functions.getOwner().call();
		if not self.address == owner:
			self.ERROR("You are not the pool owner; this transaction will fail.");
			return(False);

		fn = pool.functions.startAmplificationParameterUpdate(rawEndValue, endTime);
		tx = self.buildTx(fn, gasFactor, gasPriceSpeed, nonceOverride, gasEstimateOverride, gasPriceGweiOverride);
		txHash = self.sendTx(tx, isAsync);
		return(txHash);

	# https://dev.balancer.fi/references/contracts/apis/pools/weightedpool2tokens#gettimeweightedaverage
	def balOraclePoolGetTimeWeightedAverage(self, poolId, queries):
		poolAddress = self.web3.toChecksumAddress(poolId[:42]);
		pool = self.web3.eth.contract(address=poolAddress, abi=self.balPoolGetAbi("WeightedPool2Tokens"));
		results = pool.functions.getTimeWeightedAverage(queries).call();
		return(results);

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

	def balDoSwap(self, swapDescription, isAsync=False, gasFactor=1.05, gasPriceSpeed="average", nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):
		swapFn = self.balCreateFnSwap(swapDescription);
		tx = self.buildTx(swapFn, gasFactor, gasPriceSpeed, nonceOverride, gasEstimateOverride, gasPriceGweiOverride);
		txHash = self.sendTx(tx, isAsync);
		return(txHash);

	def balDoBatchSwap(self, swapDescription, isAsync=False, gasFactor=1.05, gasPriceSpeed="average", nonceOverride=-1, gasEstimateOverride=-1, gasPriceGweiOverride=-1):
		batchSwapFn = self.balCreateFnBatchSwap(swapDescription);
		tx = self.buildTx(batchSwapFn, gasFactor, gasPriceSpeed, nonceOverride, gasEstimateOverride, gasPriceGweiOverride);
		txHash = self.sendTx(tx, isAsync);
		return(txHash);

	def balCreateFnSwap(self, swapDescription):
		kind = int(swapDescription["kind"])
		limitedToken = None;
		amountToken = None;
		if kind == 0: #GIVEN_IN
			amountToken = swapDescription["assetIn"];
			limitedToken = swapDescription["assetOut"];
		elif kind == 1: #GIVEN_OUT
			amountToken = swapDescription["assetOut"];
			limitedToken = swapDescription["assetIn"];

		amountWei = int(Decimal(swapDescription["amount"]) * 10 ** Decimal(self.erc20GetDecimals(amountToken)));
		limitWei = int(Decimal(swapDescription["limit"]) * 10 ** Decimal(self.erc20GetDecimals(limitedToken)));

		swapStruct = (
			swapDescription["poolId"],
			kind,
			self.web3.toChecksumAddress(swapDescription["assetIn"]),
			self.web3.toChecksumAddress(swapDescription["assetOut"]),
			amountWei,
			self.balSwapGetUserData(None)
		)
		fundStruct = (
			self.web3.toChecksumAddress(swapDescription["fund"]["sender"]),
			swapDescription["fund"]["fromInternalBalance"],
			self.web3.toChecksumAddress(swapDescription["fund"]["recipient"]),
			swapDescription["fund"]["toInternalBalance"]
		)
		vault = self.balLoadContract("Vault");
		singleSwapFunction = vault.functions.swap(
			swapStruct,
			fundStruct,
			limitWei,
			int(swapDescription["deadline"])
		)
		return(singleSwapFunction);

	def balFormatBatchSwapData(self, swapDescription):
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

			idxTokenAmount = idxSortedIn;
			if kind == 1:
				idxTokenAmount = idxSortedOut;

			decimals = self.erc20GetDecimals(sortedTokens[idxTokenAmount]);
			amount = int( Decimal(swap["amount"]) * Decimal(10**(decimals)));

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
		return(kind, swapsTuples, assets, funds, intReorderedLimits, deadline);

	def balCreateFnBatchSwap(self, swapDescription):
		(kind, swapsTuples, assets, funds, intReorderedLimits, deadline) = self.balFormatBatchSwapData(swapDescription);
		vault = self.balLoadContract("Vault");
		batchSwapFunction = vault.functions.batchSwap(	kind,
														swapsTuples,
														assets,
														funds,
														intReorderedLimits,
														deadline);
		return(batchSwapFunction);

	def balQueryBatchSwaps(self, originalSwapsDescription):
		swapsDescription = copy.deepcopy(originalSwapsDescription);
		vault = self.balLoadContract("Vault");
		for swapDescription in swapsDescription:

			# do deep copy to avoid modifying the swapDescription in place, breaking index remappings
			deepCopySwapDescription = copy.deepcopy(swapDescription);
			(kind, swapsTuples, assets, funds, intReorderedLimits, deadline) = self.balFormatBatchSwapData(deepCopySwapDescription);
			args = [kind, swapsTuples, assets, funds];
			self.mc.addCall(vault.address, vault.abi, "queryBatchSwap", args=args);
		(data, successes) = self.mc.execute();

		outputs = [];
		for swapDescription, outputData, currSuccess in zip(swapsDescription, data, successes):
			output = None;
			if currSuccess:
				amounts = list(outputData[0]);
				output = {};
				for asset, amount in zip(assets, amounts):
					decimals = self.erc20GetDecimals(asset);
					output[asset] = amount * 10**(-decimals);
			else:
				output = {asset:None for asset in assets};
			outputs.append(output);

		return(outputs);

	def balQueryBatchSwap(self, originalSwapDescription):
		swapDescription = copy.deepcopy(originalSwapDescription);
		(kind, swapsTuples, assets, funds, intReorderedLimits, deadline) = self.balFormatBatchSwapData(swapDescription);
		vault = self.balLoadContract("Vault");
		amounts = vault.functions.queryBatchSwap(		kind,
														swapsTuples,
														assets,
														funds).call();

		output = {};
		for asset, amount in zip(assets, amounts):
			decimals = self.erc20GetDecimals(asset);
			output[asset] = amount * 10**(-decimals);
		return(output);

	def balGetLinkToFrontend(self, poolId):
		if "balFrontend" in self.networkParams[self.network].keys():
			return("https://" + self.networkParams[self.network]["balFrontend"] + "pool/0x" + poolId);
		else:
			return("")

	def multiCallErc20BatchDecimals(self, tokens):
		self.mc.reset();
		payload = [];
		for token in tokens:
			currTokenContract = self.erc20GetContract(token);
			self.mc.addCall(currTokenContract.address, currTokenContract.abi, 'decimals');

		# make the actual call to MultiCall
		(outputData, successes) = self.mc.execute();
		tokensToDecimals = {};

		for token, odBytes in zip(tokens, outputData):
			decimals = odBytes[0];
			tokensToDecimals[token] = decimals;
			self.decimals[token] = decimals;
		return(tokensToDecimals);

	def getOnchainData(self, pools):
		# reset multicaller
		self.mc.reset();

		# load the vault contract
		vault = self.balLoadContract("Vault");
		target = vault.address;

		poolAbis = {};
		for poolType in pools.keys():
			poolAbis[poolType] = self.balPoolGetAbi(poolType);

		payload = [];
		pidAndFns = [];
		outputAbis = {};

		poolToType = {};
		for poolType in pools.keys():
			poolIds = pools[poolType];
			poolAbi = poolAbis[poolType];

			# construct all the calls in format (VaultAddress, encodedCallData)
			for poolId in poolIds:
				poolToType[poolId] = poolType;

				poolAddress = self.balPooldIdToAddress(poolId);
				currPool = self.balLoadArbitraryContract(poolAddress, self.mc.listToString(poolAbi))

				# === all pools have tokens and swap fee, pausedState ===
				self.mc.addCall(vault.address, vault.abi, 'getPoolTokens', args=[poolId]);
				self.mc.addCall(currPool.address, currPool.abi, 'getSwapFeePercentage');
				self.mc.addCall(currPool.address, currPool.abi, 'getPausedState');
				pidAndFns.append((poolId, "getPoolTokens"));
				pidAndFns.append((poolId, "getSwapFeePercentage"));
				pidAndFns.append((poolId, "getPausedState"));

				# === using weighted math ===
				if poolType in ["Weighted", "LiquidityBootstrapping", "Investment"]:
					self.mc.addCall(currPool.address, currPool.abi, 'getNormalizedWeights');
					pidAndFns.append((poolId, "getNormalizedWeights"));

				# === using stable math ===
				if poolType in ["Stable", "MetaStable"]:
					self.mc.addCall(currPool.address, currPool.abi, 'getAmplificationParameter');
					pidAndFns.append((poolId, "getAmplificationParameter"));

				# === have pausable swaps by pool owner ===
				if poolType in [ "LiquidityBootstrapping", "Investment"]:
					self.mc.addCall(currPool.address, currPool.abi, 'getSwapEnabled');
					pidAndFns.append((poolId, "getSwapEnabled"));

		(data, successes) = self.mc.execute();

		chainDataOut = {};
		chainDataBookkeeping = {};

		for decodedOutputData, pidAndFn in zip(data, pidAndFns):
			poolId = pidAndFn[0];
			decoder = pidAndFn[1];

			if not poolId in chainDataOut.keys():
				chainDataOut[poolId] = {"poolType":poolToType[poolId]};
				chainDataBookkeeping[poolId] = {};

			if decoder == "getPoolTokens":
				addresses = list(decodedOutputData[0]);
				balances = 	list(decodedOutputData[1]);
				lastChangeBlock = decodedOutputData[2];

				chainDataOut[poolId]["lastChangeBlock"] = lastChangeBlock;
				chainDataBookkeeping[poolId]["orderedAddresses"] = addresses;

				chainDataOut[poolId]["tokens"] = {};
				for address, balance in zip(addresses, balances):
					chainDataOut[poolId]["tokens"][address] = {"rawBalance":str(balance)};

			elif decoder == "getNormalizedWeights":
				normalizedWeights = list(decodedOutputData[0]);
				addresses = chainDataBookkeeping[poolId]["orderedAddresses"];
				for address, normalizedWeight in zip(addresses, normalizedWeights):
					weight = Decimal(str(normalizedWeight)) * Decimal(str(1e-18));
					chainDataOut[poolId]["tokens"][address]["weight"] = str(weight);

			elif decoder == "getSwapFeePercentage":
				swapFee = Decimal(decodedOutputData[0]) * Decimal(str(1e-18));
				chainDataOut[poolId]["swapFee"] = str(swapFee);

			elif decoder == "getAmplificationParameter":
				rawAmp  = Decimal(decodedOutputData[0]);
				scaling = Decimal(decodedOutputData[2]);
				chainDataOut[poolId]["amp"] = str(rawAmp/scaling);

			elif decoder == "getSwapEnabled":
				chainDataOut[poolId]["swapEnabled"] = decodedOutputData[0];

			elif decoder == "getPausedState":
				chainDataOut[poolId]["pausedState"] = decodedOutputData[0];

		#find tokens for which decimals have not been cached
		tokens = set();
		for pool in chainDataOut.keys():
			for token in chainDataOut[pool]["tokens"].keys():
				tokens.add(token);
		haveDecimalsFor = set(self.decimals.keys());

		# set subtraction (A - B) gives "What is in A that isn't in B?"
		needDecimalsFor = tokens - haveDecimalsFor;

		#if there are any, query them onchain using multicall
		if len(needDecimalsFor) > 0:
			print("New tokens found. Caching decimals for", len(needDecimalsFor), "tokens...")
			self.multiCallErc20BatchDecimals(needDecimalsFor);

		# update rawBalances to have decimal adjusted values
		for pool in chainDataOut.keys():
			for token in chainDataOut[pool]["tokens"].keys():
				rawBalance = chainDataOut[pool]["tokens"][token]["rawBalance"];
				decimals = self.erc20GetDecimals(token);
				chainDataOut[pool]["tokens"][token]["balance"] = str(Decimal(rawBalance) * Decimal(10**(-decimals)));

		return(chainDataOut);

	def generateDeploymentsDocsTable(self):
		outputString = "";
		contracts = [];
		addresses = [];

		network = self.network;
		blockExplorer = "https://" + self.networkParams[network]["blockExplorerUrl"];
		outputString += "{% tab title=\"" + network.title() + "\" %}\n"

		for contractType in self.deploymentAddresses:
			contracts.append(contractType);

			address = self.deploymentAddresses[contractType];
			etherscanPage = blockExplorer + "/address/" + address;
			addresses.append("[" + address + "](" + etherscanPage + ")");

		longestContractStringLength = getLongestStringLength(contracts);
		longestAddressStringLength = getLongestStringLength(addresses);

		contractDashLine = "".join(["-"]*longestContractStringLength);
		addressDashLine = "".join(["-"]*longestAddressStringLength);

		contracts = ["Contracts", contractDashLine] + contracts;
		addresses = ["Addresses", addressDashLine] + addresses;

		for (c,a) in zip(contracts, addresses):
			cPadded = padWithSpaces(c, longestContractStringLength);
			aPadded = padWithSpaces(a, longestAddressStringLength);
			line = "| " + cPadded + " | " + aPadded + " |\n"
			outputString += line
		outputString += "\n{% endtab %}"
		return(outputString)
