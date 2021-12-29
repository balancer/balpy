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
    client = None

    """
	A starting point for querying pool data from the Balancer Subgraph.
		At time of writing, this package does not cover all types of queries
		possible to the Balancer V2 Subgraph. It does, however, allow users
		to query pool data, among other things. Types of queries will ultimately
		grow to include all possible queries to the Balancer Subgraph.

		For more information on the Subgraph, please go to:
		https://thegraph.com/legacy-explorer/subgraph/balancer-labs/balancer-v2
	"""

    def __init__(
            self,
            network="mainnet",
            custom_url=None,
            using_json_endpoint=False):
        super(TheGraph, self).__init__()
        self.network = network
        self.init_bal_v2_graph(
            custom_url=custom_url,
            using_json_endpoint=using_json_endpoint)

    def print_json(self, curr_dict):
        print(json.dumps(curr_dict, indent=4))

    def call_custom_endpoint(self, query):

        query = query.replace("\n", " ")
        query = query.replace("\t", "")
        query_dict = {"query": query}
        serialized_data = json.dumps(query_dict)
        headers = {"Content-Type": "application/json"}
        r = requests.post(
            self.graph_url,
            data=serialized_data,
            headers=headers)
        response = r.json()
        return(response["data"])

    def assert_init(self):
        if self.client is None:
            print()
            print("[ERROR] Subgraph not initialized.")
            print("Call \"initBalV2Graph(network)\" before calling this function.")
            print()
            return(None)

    def init_bal_v2_graph(
            self,
            custom_url,
            using_json_endpoint,
            verbose=False):
        if custom_url is not None and using_json_endpoint:
            self.client = "CUSTOM"
            self.graph_url = custom_url
            return(True)

        network_string = ""
        if not self.network == "mainnet":
            network_string = "-" + self.network

        if verbose:
            print("Balancer V2 Subgraph initializing on:", self.network, "...")

        graph_url = "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer" + \
            network_string + "-v2"
        if custom_url is not None and not using_json_endpoint:
            graph_url = custom_url

        balancer_transport = RequestsHTTPTransport(
            url=graph_url,
            verify=True,
            retries=3
        )
        self.client = Client(transport=balancer_transport)

        if verbose:
            print("Successfully initialized on network:", self.network)

    def get_pool_tokens(self, pool_id, verbose=False):

        self.assert_init()

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
		'''
        formatted_query_string = pool_token_query.format(pool_id=pool_id)
        if self.client == "CUSTOM":
            response = self.call_custom_endpoint(formatted_query_string)
        else:
            response = self.client.execute(gql(formatted_query_string))
        if verbose:
            print("Got pool tokens.")
        return(response["poolTokens"])

    def get_num_pools(self, verbose=False):

        self.assert_init()
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
            response = self.call_custom_endpoint(balancers_query)
        else:
            response = self.client.execute(gql(balancers_query))

        if verbose:
            print("Got response from the Subgraph")

        for balancer in response["balancers"]:
            if balancer["id"] == "2":
                num_pools = balancer["poolCount"]
                return(num_pools)
        return None

    def get_pools(self, batch_size, skips, verbose=False):

        self.assert_init()
        if verbose:
            print(
                "Querying pools #",
                skips,
                "through #",
                skips +
                batch_size,
                "...")

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
        formatted_query_string = query_string.format(
            first=batch_size, skip=skips)
        if self.client == "CUSTOM":
            response = self.call_custom_endpoint(formatted_query_string)
        else:
            response = self.client.execute(gql(formatted_query_string))

        if verbose:
            print("Got pools.")
        return(response)

    def get_v2_pools(self, batch_size, verbose=False):

        if self.client is None:
            self.init_bal_v2_graph(verbose=verbose)

        num_pools = self.get_num_pools(verbose=verbose)
        num_calls = math.ceil(num_pools / batch_size)

        if verbose:
            print("Querying", num_pools, "pools...")

        # query all pools by batch to save time
        pool_tokens = {}
        for i in range(num_calls):
            response = self.get_pools(batch_size, batch_size * i, verbose)

            for pool in response["pools"]:
                curr_id = pool["id"]
                curr_pool_token_data = self.get_pool_tokens(
                    curr_id, verbose=verbose)
                pool_data = {}
                pool_data["tokens"] = curr_pool_token_data
                pool_data["poolType"] = pool["poolType"]
                pool_data["swapFee"] = pool["swapFee"]
                pool_tokens[curr_id] = pool_data
        return(pool_tokens)

    def get_v2_pool_i_ds(self, batch_size, verbose=False):

        if self.client is None:
            self.init_bal_v2_graph(verbose=verbose)

        num_pools = self.get_num_pools(verbose=verbose)
        num_calls = math.ceil(num_pools / batch_size)

        if verbose:
            print("Querying", num_pools, "pools...")

        # query all pools by batch to save time
        pool_ids_by_type = {}
        for i in range(num_calls):
            response = self.get_pools(batch_size, batch_size * i, verbose)
            for pool in response["pools"]:
                if pool["poolType"] not in pool_ids_by_type.keys():
                    pool_ids_by_type[pool["poolType"]] = []
                pool_ids_by_type[pool["poolType"]].append(pool["id"])
        header = {}
        header["stamp"] = time.time()
        pool_count = 0
        for t in pool_ids_by_type.keys():
            pool_count += len(pool_ids_by_type[t])
        header["numPools"] = pool_count

        data = {}
        data["header"] = header
        data["pools"] = pool_ids_by_type
        return(data)

    def get_pool_bpt_price_estimate(self, pool_id, verbose=False):

        self.assert_init()
        if verbose:
            print("Getting data for pool", pool_id, "from the subgraph...")

        query_string = '''
			query {{
				pools(where:{{id: "{pool_id}"}}) {{
					totalShares
					totalLiquidity
				}}
			}}
			'''
        formatted_query_string = query_string.format(pool_id=pool_id)
        response = self.client.execute(gql(formatted_query_string))

        pool = response["pools"][0]
        price_per_bpt = float(pool["totalLiquidity"]) / \
            float(pool["totalShares"])

        if verbose:
            print("Got price data:", price_per_bpt)
        return(price_per_bpt)


def main():

    batch_size = 30
    print()

    if len(sys.argv) < 2:
        print("Usage: python", sys.argv[0], "<network>")
        print("No network given; defaulting to mainnet Ethereum")
        network = "mainnet"
    else:
        network = sys.argv[1]

    networks = ["mainnet", "kovan", "polygon", "arbitrum"]

    if network not in networks:
        print("Network", network, "is not supported!")
        print("Supported networks are:")
        for n in networks:
            print("\t" + n)
        print("Quitting")
        quit()

    verbose = True

    graph = TheGraph(network)
    # pools = graph.get_num_pools(verbose=verbose)
    pools = graph.get_v2_pools(batch_size, verbose=verbose)
    graph.print_json(pools)


if __name__ == '__main__':
    main()