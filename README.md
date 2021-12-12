![balpy](images/balpy.png?raw=true "balpy")
# balpy
## Python tools for interacting with Balancer Protocol V2 in Python. 

DISCLAIMER: While balpy is intended to be a useful tool to simplify interacting with Balancer V2 Smart Contracts, this package is an ALPHA-build and should be considered as such. Use at your own risk! This package is capable of sending Ethereum (or EVM compatible) tokens controlled by whatever private key you provide. User assumes all liability for using this software; contributors to this package are not liable for any undesirable results. Users are STRONGLY encouraged to experiment with this package on testnets before using it on mainnet with valuable assets.

## Usage
balpy has been tested on:
- MacOS using Python 3.9.0
- Linux using Python 3.9-dev
- Windows using Python 3.9.5

### Install
Local installation of the latest balpy release can be done simply using:
```bash
pip install balpy
```
However, we recommend creating a package through poetry
```bash
poetry new package-name
cd package-name
poetry add balpy
```

See release on PyPI: https://pypi.org/project/balpy/

### Build from source

```bash
# If you do not have poetry installed, install it using the following commands:
pip install poetry
# Install in virtual environment using poetry
git clone https://github.com/balancer-labs/balpy.git
cd balpy
poetry install
# You can enter the virtual environment using
poetry shell
```

### Environment Variables
You must set these two environment variables in order to use the balpy module
- KEY_API_ETHERSCAN: 	API key for Etherscan for gas prices
- KEY_PRIVATE: 			Plain text private key for signing transactions

You also must set AT LEAST one of these environment variables to connect to the network
- KEY_API_INFURA: 		API key for Infura for sending transactions
- BALPY_CUSTOM_RPC:   Custom RPC URL (like localhost or Polygon RPC)


## Samples
See README.md in samples/ for more information.
