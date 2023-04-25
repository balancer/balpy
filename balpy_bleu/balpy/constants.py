from enum import Enum

class Chain(Enum):
    mainnet = 1
    polygon = 137
    arbitrum = 42161
    gnosis = 100
    optimism = 10
    goerli = 5

    def __init__(self, id):
        self.id = id


class VaultAddress(Enum):
    mainnet = 1
    polygon = 137
    arbitrum = 42161
    gnosis = 100
    optimism = 10
    goerli = 5


VAULT_ADDRESSES = {
    Chain.mainnet: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    Chain.polygon: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    Chain.arbitrum: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    Chain.gnosis: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    Chain.optimism: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    Chain.goerli: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
}
    