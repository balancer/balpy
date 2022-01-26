# <img src="https://github.com/balancer-labs/balancer-core-v2/blob/master/logo.svg" alt="Balancer" height="128px">

## Overview

The BalancerV2 model is a python implementation of the balancerv2 protocol funded by Balancer and the Token Engineering community. In collaboration with Ocean Protocol and PowerPool. 
We hope to build a resiliant, easy, and simple to use access to balancer pools for simulations, and build a brighter tomorrow for Token Engineers. Feel free to play and use this model for your own simulations and grow token engineering everywhere.

- Copy BalancerV2 Pools from on chain, being able to pull weights from chain based on the symbols provided, this will reduce friction for new users.
- Ease access into BalancerV2 pools for anyone wanting to make a trade and see the ending result of the pool
- Provide an interface for easy swapping, adding liquidity, and removing it. This can be done with ipython or Jupyter
- Develop rigorous testing for math functions to assure decimals are flowing exactly as EVM
- Model ecosystem with agents using these balancer pools as an interactive objects.

All research is open source and transparent. For more information please visit the [BalancerV2 Simulations Documentation](https://metavision-labs.gitbook.io/balancerv2cad/).

## Balancer V2 Model

Installation 
```
pip install balancerv2cad
```

## Sample Usage
```
from balancerv2cad.WeightedPool import WeightedPool
wp = WeightedPool()
# amounts of tokens to join pool, weights of tokens
wp.join_pool({'WETH':19609,'DAI':30776582},{'WETH':0.6,'DAI':0.4})
wp.swap('WETH','DAI',2)
```

