from decimal import Decimal
from balancerv2cad.WeightedMath import WeightedMath
from balancerv2cad.BalancerConstants import *


class WeightedPool(WeightedMath):

    def __init__(self, initial_pool_supply: Decimal = INIT_POOL_SUPPLY):
        self._swap_fee = MIN_FEE
        self.total_weight = Decimal('0')
        self._pool_token_supply = initial_pool_supply
        self.factory_fees = {}
        self._balances = {}
        self._weights = {}


    def swap(self, token_in: str, token_out: str, amount: Decimal, given_in: bool = True):
        if(isinstance(amount,int) or isinstance(amount,float)):
            amount = Decimal(amount)
        elif(not isinstance(amount, Decimal)):
            raise Exception("INCORRECT_TYPE")
        factory_fee = amount*self._swap_fee
        swap_amount = amount - factory_fee
        self.factory_fees[token_in] += factory_fee
        balances = [self._balances[token_in], self._balances[token_out]]
        weights = [self._weights[token_in], self._weights[token_out]]
        
        if(given_in):
            amount_out = WeightedMath.calc_out_given_in(balances[0], weights[0], balances[1], weights[1], swap_amount)
            self._balances[token_out] -= amount_out
            self._balances[token_in] += swap_amount
            
        else:
            amount_in = WeightedMath.calc_in_given_out(balances[0], weights[0], balances[1], weights[1], swap_amount)            
            self._balances[token_out] -= swap_amount
            self._balances[token_in] += amount_in

        return amount_out if given_in else amount_in
    
    def join_pool(self, balances: dict, weights={}):
        if(not balances.keys()==weights.keys()): raise Exception('KEYS NOT EQUAL')
        for key in weights:
            if(not isinstance(weights[key],Decimal)):
               weights[key] = Decimal(weights[key])
               self.factory_fees.update({key:Decimal(0)})
            if(not isinstance(balances[key],Decimal)):
               balances[key] = Decimal(balances[key])
            
        for key in balances:
            if key in self._balances:
                self._balances[key] += balances[key]
            else:
                self._balances.update({key:balances[key]})
        self._weights = weights

        if(len(self._balances)>8):
            raise Exception("over 8 tokens")
    
    def exit_pool(self, balances: dict):
        bals = self._balances - balances
        for key in bals:
            if(bals[key]<0): bals[key] = 0
        self._balances = bals
                 
    def set_swap_fee(self, amount: Decimal):
        if(isinstance(amount,int) or isinstance(amount,float)):
            amount = Decimal(amount)
        elif(not isinstance(amount, Decimal)):
            raise Exception("INCORRECT_TYPE")
        self._swap_fee = amount
    
    def set_weights(self, weights: dict):
        if(not weights.keys() in self._weights): raise Exception('WEIGHT TICKER NOT FOUND, JOIN POOL FIRST')
        for key in weights:
            if(isinstance(amount,int) or isinstance(amount,float)):
                amount = Decimal(amount)
            elif(not isinstance(amount, Decimal)):
                raise Exception("INCORRECT_TYPE")
            self._weights[key] = weights[key]
        
    def _mint_pool_share(self, amount: Decimal):
        self._pool_token_supply += amount
        
    def _burn_pool_share(self, amount: Decimal):
        self._pool_token_supply -= amount

    def get_balances(self):
        return self._balances

    def get_factory_fees(self):
        return self.factory_fees    

