from enum import Enum
from collections import namedtuple

_Chain = namedtuple('Chain', ['id', 'vault_address'])

class Chain(Enum):
    @property
    def vault_address(self):
        return self.value.vault_address
    
    @property
    def id(self):
        return self.value.id
    
    mainnet = _Chain(1, "0xBA12222222228d8Ba445958a75a0704d566BF2C8")
    polygon = _Chain(137, "0xBA12222222228d8Ba445958a75a0704d566BF2C8")
    arbitrum = _Chain(42161, "0xBA12222222228d8Ba445958a75a0704d566BF2C8")
    gnosis = _Chain(100, "0xBA12222222228d8Ba445958a75a0704d566BF2C8")
    optimism = _Chain(10, "0xBA12222222228d8Ba445958a75a0704d566BF2C8")
    goerli = _Chain(5, "0xBA12222222228d8Ba445958a75a0704d566BF2C8")


