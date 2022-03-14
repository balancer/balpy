from decimal import *
from typing import List
from attr import dataclass
from math import ceil, floor
from balancerv2cad.util import *

getcontext().prec = 28
@dataclass
class BalancerMathResult:
    result: Decimal
    fee: Decimal


class StableMath:

# -------------------------------------
    @staticmethod
    def calculateInvariant(amplificationParameter: Decimal, balances: list) -> Decimal:

        # /**********************************************************************************************
        # // invariant                                                                                 //
        # // D = invariant                                                  D^(n+1)                    //
        # // A = amplification coefficient      A  n^n S + D = A D n^n + -----------                   //
        # // S = sum of balances                                             n^n P                     //
        # // P = product of balances                                                                   //
        # // n = number of tokens                                                                      //
        # *********x************************************************************************************/

        bal_sum = 0
        for bal in balances:
            bal_sum += bal
        num_tokens = len(balances)
        if(bal_sum==0):
            return 0
        prevInvariant = 0
        invariant = bal_sum
        ampTimesTotal = amplificationParameter*num_tokens
        for i in range(255):
            P_D = num_tokens*balances[0]
            for j in range(1, num_tokens):
                P_D = ceil(((P_D*balances[j])*num_tokens)/invariant)
            prevInvariant = invariant

            invariant = ceil(((num_tokens*invariant)*invariant + (ampTimesTotal*bal_sum)*P_D) / ((num_tokens + 1)*invariant + (ampTimesTotal - 1)*P_D))
            if(invariant > prevInvariant):
                if(invariant - prevInvariant <= 1):
                    break
            elif(prevInvariant - invariant <= 1):
                break
        return Decimal(invariant)



    # Flow of calculations:
    #  amountsTokenOut -> amountsOutProportional ->
    #  amountOutPercentageExcess -> amountOutBeforeFee -> newInvariant -> amountBPTIn
    @staticmethod
    def calcBptInGivenExactTokensOut(amplificationParameter: Decimal, balances: list, amountsOut: list, bptTotalSupply: Decimal, swapFee: Decimal) -> Decimal:
        currentInvariants = StableMath.calculateInvariant(amplificationParameter, balances)
        # calculate the sum of all token balances
        sumBalances = Decimal(0)
        for i in range(len(balances)):
            sumBalances += balances[i]

        tokenBalanceRatiosWithoutFee = [None] * len(balances)
        weightedBalanceRatio = Decimal(0)

        getcontext().prec = 28
        for i in range(len(balances)):
            currentWeight = divUp(balances[i], sumBalances)
            tokenBalanceRatiosWithoutFee[i] = balances[i] - divUp(amountsOut[i], balances[i])
            weightedBalanceRatio = weightedBalanceRatio + mulUp(tokenBalanceRatiosWithoutFee[i], currentWeight)

        newBalances = []
        for i in range(len(balances)):
            tokenBalancePercentageExcess = 0
            if weightedBalanceRatio <= tokenBalanceRatiosWithoutFee[i]:
                tokenBalancePercentageExcess = 0
            else:
                tokenBalancePercentageExcess = weightedBalanceRatio - Decimal(divUp(tokenBalanceRatiosWithoutFee[i], Decimal(complement(tokenBalanceRatiosWithoutFee[i]))))

            swapFeeExcess = mulUp(swapFee, Decimal(tokenBalancePercentageExcess))
            amountOutBeforeFee = Decimal(divUp(amountsOut[i], complement(swapFeeExcess)))
            newBalances.append(balances[i] - amountOutBeforeFee)

        # get the new invariant, taking Decimalo account swap fees
        newInvariant = StableMath.calculateInvariant(amplificationParameter, newBalances)

        # return amountBPTIn
        return bptTotalSupply * Decimal(divUp(newInvariant, complement(currentInvariants)))


    @staticmethod
    def calcBptOutGivenExactTokensIn(amplificationParameter: Decimal, balances: list, amountsIn: list, bptTotalSupply: Decimal, swapFee: Decimal, swapFeePercentage: Decimal) -> Decimal:
        # get current invariant
        currentInvariant = StableMath.calculateInvariant(amplificationParameter, balances)

        sumBalances = Decimal(0)
        for i in range(len(balances)):
            sumBalances += balances[i]

        # Calculate the weighted balance ratio without considering fees
        tokenBalanceRatiosWithoutFee = []
        weightedBalanceRatio = 0
        for i in range(len(balances)):
            currentWeight = divDown(Decimal(balances[i]), Decimal(sumBalances))
            tokenBalanceRatiosWithoutFee.append(balances[i] + divDown(Decimal(amountsIn[i]), Decimal(balances[i])))
            weightedBalanceRatio = weightedBalanceRatio + mulDown(tokenBalanceRatiosWithoutFee[i], currentWeight)

        tokenBalancePercentageExcess = Decimal(0)
        newBalances = []
        for i in range(len(balances)):
            if weightedBalanceRatio >= tokenBalanceRatiosWithoutFee[i]:
                tokenBalancePercentageExcess = Decimal(0)
            else:
                tokenBalancePercentageExcess = tokenBalanceRatiosWithoutFee[i] - divUp(weightedBalanceRatio, (tokenBalanceRatiosWithoutFee[i]))

            swapFeeExcess = mulUp(Decimal(swapFeePercentage), tokenBalancePercentageExcess)
            amountInAfterFee = mulDown(Decimal(amountsIn[i]), Decimal(complement(swapFeeExcess)))
            newBalances.append(balances[i] + amountInAfterFee)

        # get new invariant, taking swap fees Decimalo account

        newInvariant = Decimal(StableMath.calculateInvariant(amplificationParameter, newBalances))
        # return amountBPTOut
        return Decimal(mulDown(bptTotalSupply, divDown(newInvariant, currentInvariant))) # TODO omitted subtracting ONE from current_invariant

    @staticmethod


    def calcDueTokenProtocolSwapFeeAmount(amplificationParameter: Decimal, balances: list, lastInvariant: Decimal, tokenIndex: int, protocolSwapFeePercentage: float) -> Decimal:
        # /**************************************************************************************************************
        # // oneTokenSwapFee - polynomial equation to solve                                                            //
        # // af = fee amount to calculate in one token                                                                 //
        # // bf = balance of fee token                                                                                 //
        # // f = bf - af (finalBalanceFeeToken)                                                                        //
        # // D = old invariant                                            D                     D^(n+1)                //
        # // A = amplification coefficient               f^2 + ( S - ----------  - D) * f -  ------------- = 0         //
        # // n = number of tokens                                    (A * n^n)               A * n^2n * P              //
        # // S = sum of final balances but f                                                                           //
        # // P = product of final balances but f                                                                       //
        # *******
        finalBalanceFeeToken = StableMath.getTokenBalanceGivenInvariantAndAllOtherBalances(
            amplificationParameter,
            balances,
            lastInvariant,
            tokenIndex)

        if(balances[tokenIndex] > finalBalanceFeeToken):
            accumulatedTokenSwapFees = balances[tokenIndex] - finalBalanceFeeToken
        else:
            accumulatedTokenSwapFees = 0

        return divDown(mulDown(accumulatedTokenSwapFees, Decimal(protocolSwapFeePercentage)))

    @staticmethod
    def calcInGivenOut(amplificationParameter: Decimal, balances: list, tokenIndexIn: int, tokenIndexOut: int, tokenAmountOut: Decimal) -> Decimal:

        # /**************************************************************************************************************
        # // inGivenOut token x for y - polynomial equation to solve                                                   //
        # // ax = amount in to calculate                                                                               //
        # // bx = balance token in                                                                                     //
        # // x = bx + ax (finalBalanceIn)                                                                              //
        # // D = invariant                                                D                     D^(n+1)                //
        # // A = amplification coefficient               x^2 + ( S - ----------  - D) * x -  ------------- = 0         //
        # // n = number of tokens                                     (A * n^n)               A * n^2n * P             //
        # // S = sum of final balances but x                                                                           //
        # // P = product of final balances but x                                                                       //
        # **************************************************************************************************************/
        getcontext().prec = 28
        invariant = StableMath.calculateInvariant(amplificationParameter, balances)
        balances[tokenIndexOut] = balances[tokenIndexOut] - tokenAmountOut

        finalBalanceIn = StableMath.getTokenBalanceGivenInvariantAndAllOtherBalances(
            amplificationParameter,
            balances,
            invariant,
            tokenIndexIn
        )

        balances[tokenIndexOut] = balances[tokenIndexOut]+ tokenAmountOut
        result = finalBalanceIn - balances[tokenIndexIn] + Decimal(1/1e18)
        return result

    @staticmethod


    def calcOutGivenIn(amplificationParameter: Decimal, balances: list, tokenIndexIn: int, tokenIndexOut: int, tokenAmountIn: Decimal) -> Decimal:

        # /**************************************************************************************************************
        # // outGivenIn token x for y - polynomial equation to solve                                                   //
        # // ay = amount out to calculate                                                                              //
        # // by = balance token out                                                                                    //
        # // y = by - ay (finalBalanceOut)                                                                             //
        # // D = invariant                                               D                     D^(n+1)                 //
        # // A = amplification coefficient               y^2 + ( S - ----------  - D) * y -  ------------- = 0         //
        # // n = number of tokens                                    (A * n^n)               A * n^2n * P              //
        # // S = sum of final balances but y                                                                           //
        # // P = product of final balances but y                                                                       //
        # **************************************************************************************************************/
        print("Context", "OUTGIVENIN" )
        invariant = StableMath.calculateInvariant(amplificationParameter, balances)
        print("Invariant", invariant)
        balances[tokenIndexIn] = balances[tokenIndexIn] + tokenAmountIn
        finalBalanceOut = StableMath.getTokenBalanceGivenInvariantAndAllOtherBalances(amplificationParameter, balances, invariant, tokenIndexOut)

        print("FinalBalance Out", finalBalanceOut)

        balances[tokenIndexIn] = balances[tokenIndexIn] - tokenAmountIn

        result = balances [tokenIndexOut] - finalBalanceOut  # TODO took out .sub(1) at the end of this statement

        print(result)
        print("END-CONTEXT", "OUTGIVENIN" )

        return result
        # Flow of calculations:
        #  amountBPTOut -> newInvariant -> (amountInProportional, amountInAfterFee) ->
        #  amountInPercentageExcess -> amountIn

    @staticmethod


    def calcTokenInGivenExactBptOut(amplificationParameter: Decimal, balances: list, tokenIndex: int, bptAmountOut: Decimal, bptTotalSupply: Decimal, swapFeePercentage: Decimal) -> Decimal:
        # Token in so we round up overall

        #Get the current invariant
        currentInvariant = Decimal(StableMath.calculateInvariant(amplificationParameter, balances))

        # Calculate new invariant
        newInvariant = divUp((bptTotalSupply + bptAmountOut), mulUp(bptTotalSupply, currentInvariant))

        # First calculate the sum of all token balances, which will be used
        # to calculate the current weight of each token
        sumBalances = Decimal(0)
        for i in range(len(balances)):
            sumBalances += balances[i]

        # get amountInAfterFee
        newBalanceTokenIndex = StableMath.getTokenBalanceGivenInvariantAndAllOtherBalances(amplificationParameter, balances, newInvariant, tokenIndex)
        amountInAfterFee = newBalanceTokenIndex - balances[tokenIndex]

        # Get tokenBalancePercentageExcess
        currentWeight = divDown(balances[tokenIndex], sumBalances)
        tokenBalancePercentageExcess = complement(currentWeight)
        swapFeeExcess = mulUp(swapFeePercentage, tokenBalancePercentageExcess)

        return divUp(amountInAfterFee, complement(complement(swapFeeExcess)))

    @staticmethod


    def calcTokensOutGivenExactBptIn(balances: list, bptAmountIn: Decimal, bptTotalSupply: Decimal) -> list:

        # /**********************************************************************************************
        # // exactBPTInForTokensOut                                                                    //
        # // (per token)                                                                               //
        # // aO = tokenAmountOut             /        bptIn         \                                  //
        # // b = tokenBalance      a0 = b * | ---------------------  |                                 //
        # // bptIn = bpt_amount_in             \     bpt_total_supply    /                                 //
        # // bpt = bpt_total_supply                                                                      //
        # **********************************************************************************************/

        bptRatio = divDown(bptAmountIn, bptTotalSupply)
        amountsOut = []

        for i in range(len(balances)):
            amountsOut.append(mulDown(balances[i], bptRatio))

        return amountsOut

        # Flow of calculations:
        #  amountBPTin -> newInvariant -> (amountOutProportional, amountOutBeforeFee) ->
        #  amountOutPercentageExcess -> amountOut

    @staticmethod


    def calcTokenOutGivenExactBptIn(amplificationParameter, balances: list, tokenIndex: int, bptAmountIn: Decimal, bptTotalSupply: Decimal, swapFeePercentage: Decimal) -> Decimal:
        # Get current invariant
        currentInvariant = StableMath.calculateInvariant(amplificationParameter, balances)
        # calculate the new invariant
        newInvariant = bptTotalSupply - divUp(bptAmountIn, mulUp(bptTotalSupply, currentInvariant))

        # calculate the sum of all th etoken balances, which will be used to calculate
        # the current weight of each token
        sumBalances = Decimal(0)
        for i in range(len(balances)):
            sumBalances += balances[i]

        # get amountOutBeforeFee
        newBalanceTokenIndex = StableMath.getTokenBalanceGivenInvariantAndAllOtherBalances(amplificationParameter, balances, newInvariant, tokenIndex)
        amountOutBeforeFee = balances[tokenIndex] - newBalanceTokenIndex

        # calculate tokenBalancePercentageExcess
        currentWeight = divDown(balances[tokenIndex], sumBalances)
        tokenbalancePercentageExcess = complement(currentWeight)

        swapFeeExcess = mulUp(swapFeePercentage, tokenbalancePercentageExcess)

        return mulDown(amountOutBeforeFee, complement(swapFeeExcess))


    # ------------------------------------
    @staticmethod


    def getTokenBalanceGivenInvariantAndAllOtherBalances(amplificationParameter: Decimal, balances: List[Decimal], invariant: Decimal, tokenIndex: int) -> Decimal:
        getcontext().prec = 28
        ampTimesTotal = amplificationParameter * len(balances)
        bal_sum = Decimal(sum(balances))
        P_D = len(balances) * balances[0]
        for i in range(1, len(balances)):
            P_D = (P_D*balances[i]*len(balances))/invariant

        bal_sum -= balances[tokenIndex]

        c = invariant*invariant/ampTimesTotal
        c = divUp(mulUp(c, balances[tokenIndex]), P_D)
        b = bal_sum + divDown(invariant, ampTimesTotal)
        prevTokenbalance = 0
        tokenBalance = divUp((invariant*invariant+c), (invariant+b))
        for i in range(255):
            prevTokenbalance = tokenBalance
            tokenBalance = divUp((mulUp(tokenBalance,tokenBalance) + c),((tokenBalance*Decimal(2))+b-invariant))
            if(tokenBalance > prevTokenbalance):
                if(tokenBalance-prevTokenbalance <= 1/1e18):
                    break
            elif(prevTokenbalance-tokenBalance <= 1/1e18):
                break
        return tokenBalance

