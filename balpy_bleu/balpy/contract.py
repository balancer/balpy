import os

# TODO: Update imports to
from lib import get_web3_contract, get_web3_instance
from chains import Chain
from typing import List
from enums import WeightedPoolExitKind
from eth_account import Account


class Vault:
    def __init__(self, chain=Chain.mainnet):
        self.chain = chain
        self.web3 = get_web3_instance()
        self.contract = get_web3_contract(chain.vault_address)
        self.private_key = os.getenv("PRIVATE_KEY")

    def get_protocol_fees_collector(self):
        return self.contract.functions.getProtocolFeesCollector().call()


    def estimateGas(self):
        last_block = self.web3.eth.get_block("latest", full_transactions=True)
        return int(sum([tx.gas for tx in last_block.transactions]) / len(last_block.transactions))

    def balDoExitPool(self, poolId, address, exitPoolRequestTuple):
        exitPoolFunction = self.contract.functions.exitPool(poolId, address, address, exitPoolRequestTuple)
        tx = self.buildTx(exitPoolFunction)
        return self.sendTx(tx)

    def buildTx(self, fn):
        # gasEstimate = self.estimateGas()
        gasEstimate = fn.gas_estimate()
        return fn.build_transaction({
            'chainId': self.chain.id,
            'gas': gasEstimate,
            'gasPrice': self.web3.eth.gas_price,
            'nonce': self.web3.eth.get_transaction_count(self.chain.vault_address)
        })
    
    def sendTx(self, tx):
        signedTx = Account.sign_transaction(tx, self.private_key)
        return self.web3.eth.send_raw_transaction(signedTx.rawTransaction)

    def exitPool(
        self, 
        poolId: str,
        address: str,
        bptAmount: int,
        tokenList: List[str],
        exitType:str, 
        tokenOut:int = None,
        amountsOut:List[int] = [],
        query:bool = False,
        toInternalBalance:bool = True,
        minAmountsOut:List[int] = None,
        **balDoExitPoolKwargs):
        """
        poolId: Id of the pool to exit
        address: Address of the user to burn BPTs from and receive tokens to
        bpt_amount: Amount of BPTs to burn (if exit_type == "EXACT_BPT_IN_FOR_ONE_TOKEN_OUT" or "EXACT_BPT_IN_FOR_TOKENS_OUT")
                    or max amount of BPTs to burn (if exit_type == "BPT_IN_FOR_EXACT_TOKENS_OUT")
        token_list: List of token addresses of the pool
        exit_type: "EXACT_BPT_IN_FOR_ONE_TOKEN_OUT", "EXACT_BPT_IN_FOR_TOKENS_OUT", or "BPT_IN_FOR_EXACT_TOKENS_OUT"
        token_out: Index of the token (related to token_list order) to receive (if exit_type == "EXACT_BPT_IN_FOR_ONE_TOKEN_OUT")
        amounts_out: List of amounts of tokens (same order of token_list) to receive (if exit_type == "BPT_IN_FOR_EXACT_TOKENS_OUT")
        query: If True, returns the transaction object without sending the transaction
        """
        address = self.web3.to_checksum_address(address)
        requestedTuple = WeightedPoolExitKind[exitType].getExitPoolRequestTuple(self.web3, tokenList, bptAmount, tokenOut, toInternalBalance, minAmountsOut)
        return self.balDoExitPool(poolId, address, requestedTuple)



if __name__ == '__main__':
    vault = Vault()
    test_exit_0 = {
        "poolId": "0x9f1f16b025f703ee985b58ced48daf93dad2f7ef000200000000000000000063",
        "address": "0x76b0340e50BD9883D8B2CA5fd9f52439a9e7Cf58",
        "bptAmount": 1,
        "tokenList": ["0xdfcea9088c8a88a76ff74892c1457c17dfeef9c1", "0xe0c9275e44ea80ef17579d33c55136b7da269aeb"],
        "exitType": "EXACT_BPT_IN_FOR_ONE_TOKEN_OUT",
        "tokenOut": 0,
    }

    print(vault.exitPool(**test_exit_0))
