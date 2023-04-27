import json
import os
import requests as r
import web3


def get_web3_instance():
    return web3.Web3(
        web3.HTTPProvider(
            f"https://eth-goerli.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}"
        )
    )


def get_abi_from_etherscan(contract_address):
    response = r.get(
        f"https://api-goerli.etherscan.io/api?module=contract&action=getabi&address={contract_address}"
    ).json()
    return json.loads(response["result"])


def get_web3_contract(contract_address):
    w3 = get_web3_instance()
    return w3.eth.contract(
        address=w3.to_checksum_address(contract_address),
        abi=get_abi_from_etherscan(contract_address),
    )
