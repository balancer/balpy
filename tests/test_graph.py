from samples.theGraph.getPools import main as get_pools

TEST_NETWORK = "gnosis-chain"


def test_main():
    get_pools(TEST_NETWORK)


def test_kovan():
    get_pools(TEST_NETWORK)
