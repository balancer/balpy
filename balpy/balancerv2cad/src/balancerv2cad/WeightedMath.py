from decimal import Decimal
from balancerv2cad.util import *
from balancerv2cad.BalancerConstants import *
from typing import List
import sys  # todo delete later


class WeightedMath:

    @staticmethod
    def calculate_invariant(normalized_weights: List[Decimal], balances: List[Decimal]):

        # /**********************************************************************************************
        # // invariant               _____                                                             //
        # // wi = weight index i      | |      wi                                                      //
        # // bi = balance index i     | |  bi ^   = i                                                  //
        # // i = invariant                                                                             //
        # **********************************************************************************************/

        invariant = Decimal(1)
        for i in range(len(normalized_weights)):
            invariant = mulDown(invariant, (powDown(balances[i], normalized_weights[i])))
        return invariant

    @staticmethod
    def calc_out_given_in(balance_in: Decimal, 
                          weight_in: Decimal,
                          balance_out: Decimal,
                          weight_out: Decimal,
                          amount_in: Decimal) -> Decimal:

        # /**********************************************************************************************
        # // outGivenIn                                                                                //
        # // aO = amountOut                                                                            //
        # // bO = balanceOut                                                                           //
        # // bI = balanceIn              /      /            bI             \    (wI / wO) \           //
        # // aI = amountIn    aO = bO * |  1 - | --------------------------  | ^            |          //
        # // wI = weightIn               \      \       ( bI + aI )         /              /           //
        # // wO = weightOut                                                                            //
        # **********************************************************************************************/

        denominator = balance_in + amount_in
        base = divUp(balance_in, denominator)  # balanceIn.divUp(denominator);
        exponent = divDown(weight_in, weight_out)  # weightIn.divDown(weightOut);
        power = powUp(base, exponent)  # base.powUp(exponent);

        return mulDown(balance_out, complement(power))  # balanceOut.mulDown(power.complement());

    @staticmethod
    def calc_in_given_out(balance_in: Decimal,
                          weight_in: Decimal,
                          balance_out: Decimal,
                          weight_out: Decimal,
                          amount_out: Decimal):

        # /**********************************************************************************************
        # // inGivenOut                                                                                //
        # // aO = amount_out                                                                            //
        # // bO = balance_out                                                                           //
        # // bI = balance_in              /  /            bO             \    (wO / wI)      \          //
        # // aI = amount_in    aI = bI * |  | --------------------------  | ^            - 1  |         //
        # // wI = weight_in               \  \       ( bO - aO )         /                   /          //
        # // wO = weight_out                                                                            //
        # **********************************************************************************************/

        base = divUp(balance_out, (balance_out - amount_out))
        exponent = divUp(weight_out, weight_in)
        power = powUp(base, exponent)
        ratio = power - Decimal(1)
        result = mulUp(balance_in, ratio)
        return result
        
    @staticmethod
    def calc_bpt_out_given_exact_tokens_in(balances: List[Decimal], normalized_weights: List[Decimal], amounts_in: List[Decimal],
                                           bptTotalSupply: Decimal,
                                           swap_fee: Decimal):

        balance_ratios_with_fee = [None] * len(amounts_in)
        invariant_ratio_with_fees = 0
        for i in range(len(balances)):
            balance_ratios_with_fee[i] = divDown((balances[i] + amounts_in[i]), balances[i])
            invariant_ratio_with_fees = mulDown((invariant_ratio_with_fees + balance_ratios_with_fee[i]), normalized_weights[i]) #.add(balance_ratios_with_fee[i].mulDown(normalized_weights[i]));


        invariant_ratio = Decimal(1)
        for i in range(len(balances)):
            amount_in_without_fee = None

            if(balance_ratios_with_fee[i] > invariant_ratio_with_fees):
                non_taxable_amount = mulDown(balances[i], (invariant_ratio - Decimal(1)))
                taxable_amount = amounts_in[i] - non_taxable_amount
                amount_in_without_fee = non_taxable_amount + (mulDown(taxable_amount, Decimal(1) - swap_fee))
            else:
                amount_in_without_fee = amounts_in[i]


            balance_ratio = divDown((balances[i] + amount_in_without_fee), balances[i])
            invariant_ratio = mulDown(invariant_ratio, (powDown(balance_ratio, normalized_weights[i])))

        if invariant_ratio >= 1:
            return mulDown(bptTotalSupply, (invariant_ratio - Decimal(1)))
        else:
            return 0

    @staticmethod
    def calc_token_in_given_exact_bpt_out(
        balance: Decimal,
        normalized_weight: Decimal,
        bpt_amount_out: Decimal,
        bpt_total_supply: Decimal,
        swap_fee: Decimal
    ) -> Decimal:

        # /******************************************************************************************
        # // tokenInForExactBPTOut                                                                 //
        # // a = amountIn                                                                          //
        # // b = balance                      /  /    total_bpt + bptOut      \    (1 / w)       \  //
        # // bptOut = bpt_amount_out   a = b * |  | --------------------------  | ^          - 1  |  //
        # // bpt = total_bpt                   \  \       total_bpt            /                  /  //
        # // w = weight                                                                            //
        # ******************************************************************************************/

        invariant_ratio = divUp((bpt_total_supply + bpt_amount_out), bpt_total_supply)
        sys.stdout.write(f"invariant ratio {invariant_ratio}")
        balance_ratio = powUp(invariant_ratio, (divUp(Decimal(1), normalized_weight)))
        sys.stdout.write(f"normalized weight {normalized_weight}")
        amount_in_without_fee = mulUp(balance, (balance_ratio - Decimal(1)))
        taxable_percentage = complement(normalized_weight)
        taxable_amount = mulUp(amount_in_without_fee, taxable_percentage)
        non_taxable_amount = amount_in_without_fee - taxable_amount
        sys.stdout.write(f" swap fee {swap_fee}")
        return non_taxable_amount + (divUp(taxable_amount, complement(swap_fee)))

    @staticmethod
   
    def calc_bpt_in_given_exact_tokens_out(
        balances: List[Decimal],
        normalized_weights: List[Decimal],
        amounts_out: List[Decimal],
        bpt_total_supply: Decimal,
        swap_fee: Decimal
    ) -> Decimal:

        balance_ratios_without_fee = [Decimal(0)] * len(amounts_out)
        invariant_ratio_without_fees = Decimal(0)
        for i in range(len(balances)):
            balance_ratios_without_fee[i] = divUp((balances[i] - amounts_out[i]), balances[i])
            sys.stdout.write(f"{balances[i]}{amounts_out[i]}{balances[i]}{balance_ratios_without_fee} balance ratio")
            invariant_ratio_without_fees = invariant_ratio_without_fees + (mulUp(balance_ratios_without_fee[i], normalized_weights[i]))

        invariant_ratio = Decimal(1)
        for i in range(len(balances)):
            amount_out_with_fee = None
            if(invariant_ratio_without_fees > balance_ratios_without_fee[i]):
                non_taxable_amount = mulDown(balances[i], (complement(invariant_ratio_without_fees)))
                taxable_amount = amounts_out[i] - non_taxable_amount
                amount_out_with_fee = non_taxable_amount + (divUp(taxable_amount, complement(swap_fee)))
            else:
                amount_out_with_fee = amounts_out[i]
            balance_ratio = divUp((balances[i] - amount_out_with_fee), balances[i])
            invariant_ratio = mulDown(invariant_ratio, (powDown(balance_ratio, normalized_weights[i])))
        return mulUp(bpt_total_supply, complement(invariant_ratio))

    @staticmethod
   
    def calc_token_out_given_exact_bpt_in(
        balance: Decimal,
        normalized_weight: Decimal,
        bpt_amount_in: Decimal,
        bpt_total_supply: Decimal,
        swap_fee: Decimal
    ) -> Decimal:

        # /*****************************************************************************************
        # // exactBPTInForTokenOut                                                                //
        # // a = amountOut                                                                        //
        # // b = balance                     /      /    total_bpt - bptIn       \    (1 / w)  \   //
        # // bptIn = bpt_amount_in    a = b * |  1 - | --------------------------  | ^           |  //
        # // bpt = total_bpt                  \      \       total_bpt            /             /   //
        # // w = weight                                                                           //
        # *****************************************************************************************/

        invariant_ratio = divUp((bpt_total_supply - bpt_amount_in), bpt_total_supply)
        balance_ratio = powUp(invariant_ratio, (divDown(Decimal(1), normalized_weight)))
        amount_out_without_fee = mulDown(balance, complement(balance_ratio))
        taxable_percentage = complement(normalized_weight)
        taxable_amount = mulUp(amount_out_without_fee, taxable_percentage)
        non_taxable_amount = amount_out_without_fee - taxable_amount

        return non_taxable_amount + mulDown(taxable_amount, complement(swap_fee))

    @staticmethod
   
    def calc_tokens_out_given_exact_bpt_in(
        balances: List[Decimal],
        bpt_amount_in: Decimal,
        total_bpt: Decimal
    ) -> List:

        # /**********************************************************************************************
        # // exactBPTInForTokensOut                                                                    //
        # // (per token)                                                                               //
        # // aO = amountOut                  /        bptIn         \                                  //
        # // b = balance           a0 = b * | ---------------------  |                                 //
        # // bptIn = bpt_amount_in             \       total_bpt       /                                  //
        # // bpt = total_bpt                                                                            //
        # **********************************************************************************************/

        bpt_ratio = divDown(bpt_amount_in, total_bpt)
        amounts_out = [None] * len(balances)
        for i in range(len(balances)):
            amounts_out[i] = mulDown(balances[i], bpt_ratio)
        return amounts_out

    @staticmethod
   
    def calc_due_token_protocol_swap_fee_amount(
        balance: Decimal,
        normalized_weight: Decimal,
        previous_invariant: Decimal,
        current_invariant: Decimal,
        protocol_swap_fee_percentage: Decimal) -> Decimal:

        # /*********************************************************************************
        # /*  protocol_swap_fee_percentage * balanceToken * ( 1 - (previous_invariant / current_invariant) ^ (1 / weightToken))
        # *********************************************************************************/

        if current_invariant <= previous_invariant:
            return Decimal(0)

        base = divUp(previous_invariant, current_invariant)
        exponent = divDown(Decimal(1), normalized_weight)
        base = max(base, Decimal(0.7))
        power = powUp(base, exponent)
        token_accrued_fees = mulDown(balance, (complement(power)))
        return mulDown(token_accrued_fees, protocol_swap_fee_percentage)
