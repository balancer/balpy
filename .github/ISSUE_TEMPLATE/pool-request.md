---
name: Pool Request
about: Request pool creation from the Balancer Maxis/
title: 'New Pool Request: <chain and token details>'
labels: ''
assignees: ''

---

## Before you start
** Unsupported token types**
- Tokens that rebase 
  - Needs a wrapper
- Tokens that charge tx fees.

## Questions to Answer
** What style pool do you want, delete all but one**
WeightedPool, StableSwap

** What Chain(s)**

** What tokens would you like in the pool, and if weighted pool in what ratios **

Stableswap example: wstETH,rETH,ETH
WeightedPool example: wstETH(40%), BAL(40%), bb-a-usd(20%)

**If stableswap, what should the A-factor be set to**

** What should the fees be set too**

** Are any of your tokens interest baring?**

** How do you get the price per share of the interest baring token (For Example: 1 wstETH in ETH) **

** If this is a weighted pool, you can decide if you balancer to take fees on the interest baring portion of the pool, causing this pool to be a Core Pool and particpate in the [BIP-19 Brib System](https://forum.balancer.fi/t/bip-19-incentivize-core-pools-l2-usage/3329). Do you want to want your pool with interest baring tokens to be a core pool? **

** Is it OK if permission to manage the fees and a-factor are deleted to balancer governance.  This is expected for a gauge.  If not, what address should be owner of the pool **

**What is your telegram or discord name/how can we get ahold of you to get this done?**
We prefer TG.

## Now what:
Someone will get in touch with you and give a deployer address to send tokens to.  We will deposit all of the tokens provided when creating the pool.  The ratio of the tokens deposited will determine the initial price.  For this reason you need to send tokens such that depositing  them all provides a market price.  If this is a stableswap at peg, it should be equal amounts of each pool.  If this is a weighted pool, tokens should be provided such that adding them at the specified weights results in the proper market price.  Let us know if you need help with this.  A very simple example, in a 50/50 pool if 1 COIN costs .5 USDC, then you should provide something like 100 USDC and 50 COIN.  Please do not send over 500 dollars in value.

## Check list (for delpoyer)
-  [ ] Tokens Received
-  [ ] Check/Deploy rate providers
-  [ ] Pool Deployed
-  [ ] UI pull request submitted
-  [ ] Pool tokens sent back
