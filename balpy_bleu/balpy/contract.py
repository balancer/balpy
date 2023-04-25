from balpy.lib import get_web3_contract
from balpy.constants import VAULT_ADDRESSES, Chain


class Vault:
    def __init__(self, chain=Chain.mainnet):
        self.chain = chain
        self.contract = get_web3_contract(VAULT_ADDRESSES[chain])

    def get_protocol_fees_collector(self):
        return self.contract.functions.getProtocolFeesCollector().call()

    def exit_pool(self):
        return self.contract.functions.exitPool().call()
