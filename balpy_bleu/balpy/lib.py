import json
import os
from functools import cache

import requests as r
import web3


@cache
def get_web3_instance():
    return web3.AsyncWeb3(
        web3.AsyncHTTPProvider(
            f"https://eth.llamarpc.com/rpc/{os.getenv('LLAMA_PROJECT_ID')}"
        )
    )


@cache
def get_abi_from_etherscan(contract_address):
    response = r.get(
        f"https://api.etherscan.io/api?module=contract&action=getabi&address={contract_address}"
    ).json()
    return json.loads(response["result"])


@cache
def get_web3_contract(contract_address):
    w3 = get_web3_instance()
    return w3.eth.contract(
        address=w3.to_checksum_address(contract_address),
        abi=get_abi_from_etherscan(contract_address),
    )
