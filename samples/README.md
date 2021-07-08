# balpy samples
Sample scripts for using balpy to interact with on-chain Balancer V2 contracts. 

DISCLAIMER: While balpy is intended to be a useful tool to simplify interacting with Balancer V2 Smart Contracts, this package is an ALPHA-build and should be considered as such. Use at your own risk! This package is capable of sending Ethereum tokens controlled by whatever private key you provide. User assumes all liability for using this software. Users are STRONGLY encouraged to experiment with this package on testnets before using it on mainnet with valuable assets.

## Getting Started

### Install
python3 -m pip install balpy

### Environment Variables
You must set three environment variables in order to use the balpy module
- KEY_API_ETHERSCAN: 	API key for Etherscan for gas prices
- KEY_API_INFURA: 		API key for Infura for sending transactions
- KEY_PRIVATE: 			Plain text private key for signing transactions

## Samples

### Pool Creation
- Go to poolCreation/ directory
- Edit your desired pool description json
- python3 poolCreationSample.py sample{Weighted, Oracle, Stable}Pool.json

### Swaps
- Go to batchSwaps/ directory
- Edit your desired swap type json
- python3 batchSwapSample.py sample{Single, Multihop, Flash}Swap.json

### Joins
- Go to joinPool/ directory
- Edit sampleJoin.json
- python3 joinPoolSample.py sampleJoin.json

### Internal Balances
- Go to the internalBalances/ directory
- Examine and/or edit sampleInternalBalances.py
- python sampleInternalBalances.py

### Querying TheGraph
- Go to theGraph/ directory
- python getPools.py (optional: netw0ork)

### Misc 
- Go to misc/ directory
- Directory for miscellaneous useful scripts
- Edit revokeAllowances script to revoke allowances for the given network, token, and allowed address
- python3 revokeAllowances.py
- python3 vaultReadWeth.py
