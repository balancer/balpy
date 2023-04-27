import eth_abi
from typing import List

from abc import ABC, abstractmethod, abstractproperty
import enum

class WeightedPoolExitKindAbstracted(ABC):
  @staticmethod
  def getDefaultMinAmountsOut(token_list):
    return [0] * len(token_list)

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


class WeightedPoolExitKind(enum.Enum):
  EXACT_BPT_IN_FOR_ONE_TOKEN_OUT = ExactBptInForOneTokenOut()

  def getExitPoolRequestTuple(self, *args, **kwargs):
    return self.value.getExitPoolRequestTuple(*args, **kwargs)
