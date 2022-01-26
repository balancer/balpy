from typing import List
from balancerv2cad.StableMath import StableMath
from decimal import *
import unittest

getcontext().prec = 21
MAX_RELATIVE_ERROR = Decimal(1e-17)

def expectEqualWithError(result: Decimal, expected: Decimal):
    if result <= expected + MAX_RELATIVE_ERROR and result >= expected - MAX_RELATIVE_ERROR:
        return True
    return False


class TestStableMath(unittest.TestCase):


    def test_calculateInvariants(self):
        '''
        Tests for instance of Decimal
        '''
        amp = Decimal(100)
        balances = [Decimal(10),Decimal(12)]
        result =  StableMath.calculateInvariant(amp, balances)
        assert isinstance(result, Decimal)
        '''
        Tests invariant for two tokens
        expected = 22
        '''
        amp = Decimal(100)
        balances = [Decimal(10),Decimal(12)]
        result =  StableMath.calculateInvariant(amp, balances)
        assert expectEqualWithError(result, Decimal(22))
        '''
        Tests invariant for three tokens
        expected = 22
        '''
        amp = Decimal(100)
        balances = [Decimal(10),Decimal(12), Decimal(14)]
        result =  StableMath.calculateInvariant(amp, balances)
        assert expectEqualWithError(result, Decimal(36))

    def test_calcInGivenOut(stablemath_test):
       #TODO assert StableMath.calcInGivenOut(2,[222,3112,311],1,1,4) == 0.000002756210410895
        '''
        Tests for instance of Decimal
        '''
        amp = Decimal(100)
        balances = [Decimal(10), Decimal(12), Decimal(14)]
        tokenIndexIn = 0
        tokenIndexOut = 1
        tokenAmountOut = Decimal(1)
        result = StableMath.calcInGivenOut(amp, balances, tokenIndexIn, tokenIndexOut, tokenAmountOut)
        assert isinstance(result, Decimal)
        '''
        Tests in given out for two tokens
        '''
        amp = Decimal(100)

        balances = [Decimal(10), Decimal(12)]
        tokenIndexIn = 0
        tokenIndexOut = 1
        tokenAmountOut = Decimal(1)
        result = StableMath.calcInGivenOut(amp, balances, tokenIndexIn, tokenIndexOut, tokenAmountOut)
        assert expectEqualWithError(result, Decimal(1))
        '''
        Tests in given out for three tokens
        '''
        amp = Decimal(100)

        balances = [Decimal(10), Decimal(12), Decimal(14)]
        tokenIndexIn = 0
        tokenIndexOut = 1
        tokenAmountOut = Decimal(1)
        result = StableMath.calcInGivenOut(amp, balances, tokenIndexIn, tokenIndexOut, tokenAmountOut)
        expected = Decimal(1002381999332076302)/Decimal(1e18)
        assert expectEqualWithError(result, expected)
        

    def test_calcOutGivenIn(stablemath_test):
        #    def calcOutGivenIn(amplificationParameter: Decimal, balances: list[Decimal], tokenIndexIn: int, tokenIndexOut: int, tokenAmountIn: Decimal):
        amp = Decimal(10)
        balances = [Decimal(10), Decimal(11), Decimal(12)]
        tokenIndexIn = 0
        tokenIndexOut = 1
        tokenAmountIn = Decimal(1)
        result = StableMath.calcOutGivenIn(amp, balances, tokenIndexIn, tokenIndexOut, tokenAmountIn)
        assert isinstance(result, Decimal)
        '''
        Tests out given in for two tokens
        '''
        amp = Decimal(10)
        balances = [Decimal(10), Decimal(11)]
        tokenIndexIn = 0
        tokenIndexOut = 1
        tokenAmountIn = Decimal(1)
        result = StableMath.calcOutGivenIn(amp, balances, tokenIndexIn, tokenIndexOut, tokenAmountIn)
        expected = Decimal(997840816806192585)/Decimal(1e18)
        assert expectEqualWithError(result, expected)
        '''
        Tests out given in for three tokens
        '''
        amp = Decimal(10)
        balances = [Decimal(10), Decimal(11), Decimal(12)]
        tokenIndexIn = 0
        tokenIndexOut = 1
        tokenAmountIn = Decimal(1)
        result = StableMath.calcOutGivenIn(amp, balances, tokenIndexIn, tokenIndexOut, tokenAmountIn)
        expected = Decimal(991747876655227989)/Decimal(1e18)
        assert expectEqualWithError(result, expected)
    # def test_calcDueTokenProtoclSwapFeeAmount(stablemath_test):
    #     '''
    #     Tests if output is instance of Decimal
    #     '''
    #     #TODO
    #     amp = Decimal(100)
    #     balances = [Decimal(10), Decimal(11)]
    #     lastInvariant = Decimal(10)
    #     tokenIndex = 0
    #     protocolSwapFeePercentage = 0.1
    #     result = StableMath.calcDueTokenProtocolSwapFeeAmount(amp,balances, lastInvariant, tokenIndex, protocolSwapFeePercentage)
    #     assert isinstance(result, Decimal)
    #     expectedFeeAmount = StableMath.calc
    #     assert expectEqualWithError(result, Decimal)
    def test_calcBptOutGivenExactTokensIn(stablemath_test):
        '''
        Tests for instance of Decimal
        '''
        amp = Decimal(22)
        balances = [Decimal(2), Decimal(3),Decimal(4), Decimal(20)]
        amountsIn = [Decimal(2), Decimal(1), Decimal(2), Decimal(1000)]
        bptTotalsupply = Decimal(10)
        swapFee = Decimal(2)
        swapFeePercentage = Decimal(.04)
        result = StableMath.calcBptOutGivenExactTokensIn(amp, balances, amountsIn,bptTotalsupply, swapFee,swapFeePercentage)
        assert isinstance(result, Decimal)
        '''
        '''


    def test_calcTokenInGivenExactBptOut(stablemath_test):
        amp = Decimal(100)
        balances = [Decimal(10),Decimal(11)]
        amountsOut = [Decimal(5),Decimal(6)]
        bptTotalSupply = Decimal(100)
        protocolSwapFeePercentage = Decimal(0.1)
        result = StableMath.calcBptInGivenExactTokensOut(amp, 
                                                balances,
                                                amountsOut,
                                                bptTotalSupply,
                                                protocolSwapFeePercentage)
        assert isinstance(result, Decimal)


    def test_calcTokenOutGivenExactBptIn(stablemath_test):
        balances = [Decimal(10),Decimal(11)]
        bptAmountIn = Decimal(10)
        bptTotalSupply =Decimal(2)
        result = StableMath.calcTokensOutGivenExactBptIn(balances,bptAmountIn, bptTotalSupply)
        assert isinstance(result, list)

    def test_calcTokensOutGivenExactBptIn(stablemath_test):
        balances = [Decimal(10),Decimal(11)]
        bptAmountIn = Decimal(10)
        bptTotalSupply =Decimal(2)
        result = StableMath.calcTokensOutGivenExactBptIn(balances,bptAmountIn,bptTotalSupply)
        assert isinstance(result, list)
    

    #TODO give critical results
    def test_getTokenBalanceGivenInvariantAndAllOtherBalances(stablemath_test):

        # assert StableMath.getTokenBalanceGivenInvariantAndAllOtherBalances(22, [2,3,4,20], 1, 2) == 0.002573235526125192

        # self.assertAlmostEqual(
        #     StableMath.getTokenBalanceGivenInvariantAndAllOtherBalances(
        #         Decimal(22),
        #         [Decimal(2),Decimal(3),Decimal(4),Decimal(20)],
        #         Decimal(1),
        #         2), Decimal(0.00067593918100831), 3)
        #print(TestCase.assertAlmostEqual(1,1.00000000000001,3))

        assert isinstance(StableMath.getTokenBalanceGivenInvariantAndAllOtherBalances(
            Decimal(22),
            [Decimal(2),Decimal(3),Decimal(4),Decimal(20)],
            Decimal(1),
            2), Decimal)


        amp = Decimal(10)
        balances = [Decimal(11),Decimal(11),Decimal(12)]
        invariant = Decimal(32.999999999)
        tokenIndex = 1

        result = StableMath.getTokenBalanceGivenInvariantAndAllOtherBalances(amp, balances, invariant, tokenIndex)
        assert expectEqualWithError(result, Decimal(10.008252123344772011))

        amp = Decimal(100)
        balances = [Decimal(10),Decimal(11)]
        invariant = Decimal(10)
        tokenIndex = 0

        result = StableMath.getTokenBalanceGivenInvariantAndAllOtherBalances(amp, balances, invariant, tokenIndex)
        assert expectEqualWithError(result, Decimal(0.098908137177552474646))

        amp = Decimal(100)
        balances = [Decimal(10),Decimal(11), Decimal(12)]
        invariant = Decimal(10)
        tokenIndex = 0

        result = StableMath.getTokenBalanceGivenInvariantAndAllOtherBalances(amp, balances, invariant, tokenIndex)
        assert expectEqualWithError(result, Decimal(0.00071756564425404818025))
