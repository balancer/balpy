from decimal import *
from typing import List
from balancerv2cad.StableMath import StableMath
from balancerv2cad.WeightedPool import WeightedPool
from balancerv2cad.BalancerConstants import *


class StablePool(StableMath):

    def __init__(self, initial_pool_supply: Decimal = INIT_POOL_SUPPLY):
        self._swap_fee = MIN_FEE
        self._pool_token_supply = initial_pool_supply
        self.factory_fees = Decimal('0')
        self._balances = {}

    def swap(self, token_in: str, token_out: str, amount: Decimal, given_in: bool = True):
        if(isinstance(amount,int) or isinstance(amount,float)):
            amount = Decimal(amount)
        elif(not isinstance(amount, Decimal)):
            raise Exception("INCORRECT_TYPE")
        factory_fee = amount*self._swap_fee
        swap_amount = amount - factory_fee
        self.factory_fees += factory_fee
        balances = [self._balances[token_in], self._balances[token_out]]

        if(given_in): amount_out = StableMath.calcOutGivenIn(AMPLIFICATION_PARAMETER, balances, 0, 1, swap_amount)
        else: amount_out = StableMath.calcInGivenOut(AMPLIFICATION_PARAMETER, balances, 0, 1, swap_amount)

        self._balances[token_out] -= amount_out
        self._balances[token_in] += swap_amount
        return amount_out

    def join_pool(self, balances: dict):
        if len(balances) != 2:
            raise Exception("50/50 2-token pool only")
        for key in balances:
            if key in self._balances:
                self._balances[key] += balances[key]
            else:
                self._balances.update({key:balances[key]})

    def get_amplification_parameter(self):
        return self.AMPLIFICATION_PARAMETER

    def _get_total_tokens(self):
        return len(self._balances)

    def exit_pool(self, balances: dict):
        bals = self._balances - balances
        for key in bals:
            if(bals[key]<0): bals[key] = 0
        self._balances = bals
        
    def set_swap_fee(self, amount: Decimal):
        self._swap_fee = amount

    def _mint_pool_share(self, amount: Decimal):
        self._pool_token_supply += amount

    def _burn_pool_share(self, amount: Decimal):
        self._pool_token_supply -= amount
