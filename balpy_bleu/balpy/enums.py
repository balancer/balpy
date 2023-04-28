import eth_abi
from typing import List

from abc import ABC, abstractmethod, abstractproperty
import enum

class WeightedPoolExitKindAbstracted(ABC):
  @staticmethod
  def getDefaultMinAmountsOut(token_list):
    return [0] * len(token_list)

  @staticmethod
  def getPoolAddress(w3, poolId):
    return w3._tochecksum_address(poolId[0:42])

  def converTokenToWei(self, token, amount):
    # TODO:
	def balConvertTokensToWei(self, tokens, amounts):
		rawTokens = [];
		if not len(tokens) == len(amounts):
			self.ERROR("Array length mismatch with " + str(len(tokens)) + " tokens and " + str(len(amounts)) + " amounts.");
			return(False);
		numElements = len(tokens);
		for i in range(numElements):
			token = tokens[i];
			rawValue = amounts[i];
			decimals = self.erc20GetDecimals(token);
			if rawValue == self.INFINITE or rawValue == self.MAX_UINT_112:
				decimals = 0;
			raw = int(Decimal(rawValue) * Decimal(10**decimals));
			rawTokens.append(raw);
		return(rawTokens);

  @abstractproperty
  def id():
    pass
  
  @abstractmethod
  def getUserData():
    pass

  @abstractmethod
  def sortTokenList():
    pass

  @abstractmethod
  def getExitPoolRequestTuple():
    pass


class ExactBptInForOneTokenOut(WeightedPoolExitKindAbstracted):
  id = 0

  def sortTokenList(self, w3, token_list, token_out, min_amounts_out):
    token_list_address = [w3.to_checksum_address(token) for token in token_list]
    min_amounts_out_sorted = [minAmountOut for _,minAmountOut in sorted(zip(token_list_address, min_amounts_out))]
    token_out_address = w3.to_checksum_address(token_list_address[token_out])
    token_list_address_sorted = sorted(token_list_address)
    token_out_sorted = token_list_address_sorted.index(token_out_address)
    return token_list_address_sorted, token_out_sorted, min_amounts_out_sorted

  def getUserData(self, bpt_amount, token_out):
    return eth_abi.encode(['uint256', 'uint256', 'uint256'], [self.id, bpt_amount, token_out])  

  def getExitPoolRequestTuple(self, w3, token_list, bpt_amount, token_out, to_internal_balance: bool = True, min_amounts_out: List[int]= None):
    if min_amounts_out is None:
      min_amounts_out = self.getDefaultMinAmountsOut(token_list)
    token_list, token_out, min_amounts_out = self.sortTokenList(w3, token_list, token_out, min_amounts_out)
    user_data = self.getUserData(bpt_amount, token_out)
    return (token_list, min_amounts_out, user_data, to_internal_balance)

class ExactBptInForTokensOut(WeightedPoolExitKindAbstracted):
  id = 1

  def sortTokenList(self, w3, token_list, min_amounts_out):
    token_list_address = [w3.to_checksum_address(token) for token in token_list]
    min_amounts_out_sorted = [minAmountOut for _,minAmountOut in sorted(zip(token_list_address, min_amounts_out))]
    token_list_address_sorted = sorted(token_list_address)
    return token_list_address_sorted, min_amounts_out_sorted

  def getUserData(self, bpt_amount):
    return eth_abi.encode(['uint256', 'uint256'], [self.id, bpt_amount])  

  def getExitPoolRequestTuple(self, w3, token_list, bpt_amount, to_internal_balance: bool = True, min_amounts_out: List[int]= None):
    if min_amounts_out is None:
      min_amounts_out = self.getDefaultMinAmountsOut(token_list)
    token_list, min_amounts_out = self.sortTokenList(w3, token_list, min_amounts_out)
    user_data = self.getUserData(bpt_amount)
    return (token_list, min_amounts_out, user_data, to_internal_balance)

class BptInForExactTokensOut(WeightedPoolExitKindAbstracted):
  id = 2

  def sortTokenList(self, w3, token_list, amounts_out, min_amounts_out):
    token_list_address = [w3.to_checksum_address(token) for token in token_list]
    min_amounts_out_sorted = [minAmountOut for _,minAmountOut in sorted(zip(token_list_address, min_amounts_out))]
    amounts_out_sorted = [amountOut for _,amountOut in sorted(zip(token_list_address, amounts_out))]
    token_list_address_sorted = sorted(token_list_address)
    return token_list_address_sorted, amounts_out_sorted, min_amounts_out_sorted

  def getUserData(self, amounts_out, bpt_amount):
    return eth_abi.encode(['uint256', 'uint256[]', ], [self.id, amounts_out, bpt_amount])  

  def getExitPoolRequestTuple(self, w3, token_list, bpt_amount, amounts_out, to_internal_balance: bool = True, min_amounts_out: List[int]= None):
    if min_amounts_out is None:
      min_amounts_out = self.getDefaultMinAmountsOut(token_list)
    token_list, amounts_out, min_amounts_out = self.sortTokenList(w3, token_list, amounts_out, min_amounts_out)
    user_data = self.getUserData(amounts_out, bpt_amount)
    return (token_list, min_amounts_out, user_data, to_internal_balance)




class WeightedPoolExitKind(enum.Enum):
  EXACT_BPT_IN_FOR_ONE_TOKEN_OUT = ExactBptInForOneTokenOut()
  EXACT_BPT_IN_FOR_TOKENS_OUT = ExactBptInForTokensOut()
  BPT_IN_FOR_EXACT_TOKENS_OUT = BptInForExactTokensOut()

  def getExitPoolRequestTuple(self, *args, **kwargs):
    return self.value.getExitPoolRequestTuple(*args, **kwargs)
