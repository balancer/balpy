# basics
import json
import math
import sys
import time

# thegraph queries
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# for customized endpoints
import requests

class TheGraph(object):
	client = None;
	
	"""
	A starting point for querying pool data from the Balancer Subgraph.
		At time of writing, this package does not cover all types of queries
		possible to the Balancer V2 Subgraph. It does, however, allow users 
		to query pool data, among other things. Types of queries will ultimately
		grow to include all possible queries to the Balancer Subgraph.

		For more information on the Subgraph, please go to:
		https://thegraph.com/legacy-explorer/subgraph/balancer-labs/balancer-v2
	"""

	def __init__(self, network="mainnet", customUrl=None, usingJsonEndpoint=False):
		super(TheGraph, self).__init__()
		self.network = network;
		self.initBalV2Graph(customUrl=customUrl, usingJsonEndpoint=usingJsonEndpoint);

	def printJson(self, curr_dict):
		print(json.dumps(curr_dict, indent=4))

	def callCustomEndpoint(self, query):

		query = query.replace("\n"," ");
		query = query.replace("\t","");
		queryDict = {"query":query};
		serializedData = json.dumps(queryDict);
		headers = {"Content-Type":"application/json"};
		r = requests.post(self.graphUrl, data=serializedData, headers=headers);
		response = r.json();
		return(response["data"])

	def assertInit(self):
		if self.client is None:
			print()
			print("[ERROR] Subgraph not initialized.");
			print("Call \"initBalV2Graph(network)\" before calling this function.")
			print()
			return(None);

	def initBalV2Graph(self, customUrl, usingJsonEndpoint, verbose=False):
		if not customUrl is None and usingJsonEndpoint:
			self.client = "CUSTOM"
			self.graphUrl = customUrl;
			return(True);

		network_string = "";
		if not self.network == "mainnet":
			network_string = "-" + self.network;

		if verbose:
			print("Balancer V2 Subgraph initializing on:", self.network, "...")

		graphUrl = "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer" + network_string + "-v2";
		if not customUrl is None and not usingJsonEndpoint:
			graphUrl = customUrl;

		balancer_transport=RequestsHTTPTransport(
		    url=graphUrl,
		    verify=True,
		    retries=3
		)
		self.client = Client(transport=balancer_transport)
		
		if verbose:
			print("Successfully initialized on network:", self.network);

	def getPoolTokens(self, pool_id, verbose=False):

		self.assertInit();

		if verbose:
			print("Querying tokens for pool with ID:", pool_id)

		pool_token_query = '''
		query {{
		  poolTokens(first: 8, where: {{ poolId: "{pool_id}" }}) {{
		    id
			poolId {{
				id
			}}
			symbol
			name
			decimals
			address
			balance
			invested
			investments
			weight
		  }}
		}}
		''';
		formatted_query_string = pool_token_query.format(pool_id=pool_id)
		if self.client == "CUSTOM":
			response = self.callCustomEndpoint(formatted_query_string);
		else:
			response = self.client.execute(gql(formatted_query_string))
		if verbose:
			print("Got pool tokens.")
		return(response["poolTokens"])

	def getNumPools(self, verbose=False):

		self.assertInit();
		if verbose:
			print("Querying number of pools...")

		# get number of balancer pools on v2
		balancers_query = '''
		query {
			balancers(first: 5) {
		    id
		    poolCount
		  }
		}
		'''
		if self.client == "CUSTOM":
			response = self.callCustomEndpoint(balancers_query);
		else:
			response = self.client.execute(gql(balancers_query));

		if verbose:
			print("Got response from the Subgraph")

		for balancer in response["balancers"]:
			if balancer["id"] == "2":
				num_pools = balancer["poolCount"]
				return(num_pools)
		return None;

	def getPools(self, batch_size, skips, verbose=False):

		self.assertInit();
		if verbose:
			print("Querying pools #", skips, "through #", skips + batch_size, "...")

		query_string = '''
			query {{
			  pools(first: {first}, skip: {skip}) {{
			    id
			    address
			    poolType
			    strategyType
			    swapFee
			  }}
			}}
			'''
		formatted_query_string = query_string.format(first=batch_size, skip=skips)
		if self.client == "CUSTOM":
			response = self.callCustomEndpoint(formatted_query_string);
		else:
			response = self.client.execute(gql(formatted_query_string))

		if verbose:
			print("Got pools.")
		return(response)

	def getV2Pools(self, batch_size, verbose=False):

		if self.client is None:
			self.initBalV2Graph(verbose=verbose);
		
		num_pools = self.getNumPools(verbose=verbose);
		num_calls = math.ceil(num_pools/batch_size)

		if verbose:
			print("Querying",num_pools, "pools...");

		# query all pools by batch to save time
		pool_tokens = {};
		for i in range(num_calls):
			response = self.getPools(batch_size, batch_size*i, verbose)
			
			for pool in response["pools"]:
				curr_id = pool["id"]
				curr_pool_token_data = self.getPoolTokens(curr_id, verbose=verbose);
				pool_data = {};
				pool_data["tokens"] = curr_pool_token_data;
				pool_data["poolType"] = pool["poolType"];
				pool_data["swapFee"] = pool["swapFee"];
				pool_tokens[curr_id] = pool_data;
		return(pool_tokens)

	def getV2PoolIDs(self, batch_size, verbose=False):

		if self.client is None:
			self.initBalV2Graph(verbose=verbose);

		num_pools = self.getNumPools(verbose=verbose);
		num_calls = math.ceil(num_pools/batch_size)

		if verbose:
			print("Querying",num_pools, "pools...");

		# query all pools by batch to save time
		poolIdsByType = {};
		for i in range(num_calls):
			response = self.getPools(batch_size, batch_size*i, verbose)
			for pool in response["pools"]:
				if pool["poolType"] not in poolIdsByType.keys():
					poolIdsByType[pool["poolType"]] = [];
				poolIdsByType[pool["poolType"]].append(pool["id"])
		header = {};
		header["stamp"] = time.time();
		poolCount = 0
		for t in poolIdsByType.keys():
			poolCount += len(poolIdsByType[t])
		header["numPools"] = poolCount;

		data = {};
		data["header"] = header;
		data["pools"] = poolIdsByType
		return(data)

	def getPoolBptPriceEstimate(self, poolId, verbose=False):

		self.assertInit();
		if verbose:
			print("Getting data for pool", poolId, "from the subgraph...")

		query_string = '''
			query {{
				pools(where:{{id: "{poolId}"}}) {{
					totalShares
					totalLiquidity
				}}
			}}
			'''
		formatted_query_string = query_string.format(poolId=poolId);
		response = self.client.execute(gql(formatted_query_string));

		pool = response["pools"][0]
		pricePerBpt = float(pool["totalLiquidity"])/float(pool["totalShares"])

		if verbose:
			print("Got price data:", pricePerBpt)
		return(pricePerBpt)

	def getPoolsAndTokens(self, batch_size, skips, verbose=False):
		self.assertInit();
		query_string = '''
			query {{
			  pools(first: {first}, skip: {skip}) {{
			    id
			    tokens {{
			      token
			      {{
			        id
			      }}
			    }}
			  }}
			}}
		'''
		formatted_query_string = query_string.format(first=batch_size, skip=skips)

		response = self.client.execute(gql(formatted_query_string));
		if self.client == "CUSTOM":
			response = self.callCustomEndpoint(formatted_query_string);
		else:
			response = self.client.execute(gql(formatted_query_string))
		return(response)

def main():
	
	batch_size = 30;
	print();

	if len(sys.argv) < 2:
		print("Usage: python", sys.argv[0], "<network>");
		print("No network given; defaulting to mainnet Ethereum")
		network = "mainnet"
	else:
		network = sys.argv[1];
	
	networks = ["mainnet", "kovan", "polygon", "arbitrum"];

	if not network in networks:
		print("Network", network, "is not supported!");
		print("Supported networks are:");
		for n in networks:
			print("\t" + n);
		print("Quitting")
		quit();

	verbose = True;

	graph = TheGraph(network)
	# pools = graph.getNumPools(verbose=verbose)
	pools = graph.getV2Pools(batch_size, verbose=verbose)
	graph.printJson(pools)

if __name__ == '__main__':
	main();
