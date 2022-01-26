from decimal import *
from balancerv2cad.WeightedMath import WeightedMath


getcontext().prec = 28
MAX_RELATIVE_ERROR = Decimal(1e-17)

def expectEqualWithError(result: Decimal, expected: Decimal):
    if result <= expected + MAX_RELATIVE_ERROR and result >= expected - MAX_RELATIVE_ERROR:
        return True
    return False

class TestWeightedMath:

	def test_calculate_invariant(weightedmath_test):
		#Test instance of Decimal
		normalized_weight = [Decimal(0.3), Decimal(0.2), Decimal(0.5)]
		balances = [Decimal(10), Decimal(12), Decimal(14)]
		result = WeightedMath.calculate_invariant(normalized_weight, balances)
		assert isinstance(result, Decimal)

	def test_calculate_invariant_zero_invariant(weightedmath_test):
		#Tests zero Invariant
		result = WeightedMath.calculate_invariant([Decimal(1)], [Decimal(0)])
		assert result == Decimal(0)

	def test_calculate_invariant_two_tokens(weightedmath_test):
		#Test two tokens
		normalized_weight = [Decimal(0.3), Decimal(0.7)]
		balances = [Decimal(10), Decimal(12)]
		result = WeightedMath.calculate_invariant(normalized_weight, balances)
		expected = Decimal(11.361269771988886911)
		assert expectEqualWithError(result, expected)

	def test_calculate_invariant_three_tokens(weightedmath_test):
		#Test three tokens
		normalized_weight = [Decimal(0.3), Decimal(0.2), Decimal(0.5)]
		balances = [Decimal(10), Decimal(12), Decimal(14)]
		result = WeightedMath.calculate_invariant(normalized_weight, balances)
		expected = Decimal(12.271573899486561654)
		assert expectEqualWithError(result, expected)

	def test_out_given_in_single_swap(weightedmath_test):
		#Test instance of Decimal
		token_balance_in = Decimal(100)
		token_weight_in = Decimal(50)
		token_balance_out = Decimal(100)
		token_weight_out = Decimal(40)
		token_amount_out = Decimal(15)
		result = WeightedMath.calc_out_given_in(token_balance_in, token_weight_in, token_balance_out, token_weight_out, token_amount_out)
		assert isinstance(result, Decimal)

		#Test out given in 
		expected = Decimal(1602931431298673722)/Decimal(1e17)
		assert expectEqualWithError(result, expected)

	def test_in_given_out_single_swap(weightedmath_test):
		#Test instance of Decimal
		balance_in = Decimal(100)
		weight_in = Decimal(50)
		balance_out = Decimal(100)
		weight_out = Decimal(40)
		amount_out = Decimal(15)
		result = WeightedMath.calc_in_given_out(balance_in, weight_in, balance_out, weight_out, amount_out)
		assert isinstance(result, Decimal)
		
		expected = Decimal(1388456294146839515)/Decimal(1e17)
		assert expectEqualWithError(result, expected)
	
	def test_out_given_in_extreme_amounts(weightedmath_test):
		# Test instance of Decimal

		token_balance_in = Decimal(100)
		token_weight_in = Decimal(50)
		token_balance_out = Decimal(100)
		token_weight_out = Decimal(40)
		token_amount_out = Decimal(0.00000000001)
		result = WeightedMath.calc_out_given_in(token_balance_in, token_weight_in, token_balance_out, token_weight_out, token_amount_out)

		assert isinstance(result, Decimal)

		# Test out given in 
		# min amount in

		expected = Decimal(12500000)/Decimal(1e18)
		assert expectEqualWithError(result, expected)
	def test_in_given_out_extreme_amounts(weightedmath_test):
		#Test instance of Decimal
		token_balance_in = Decimal(100)
		token_weight_in = Decimal(50)
		token_balance_out = Decimal(100)
		token_weight_out = Decimal(40)
		token_amount_out = Decimal(0.00000000001)
		result = WeightedMath.calc_in_given_out(token_balance_in, token_weight_in, token_balance_out, token_weight_out, token_amount_out)

		assert isinstance(result, Decimal)

		# Test In given in 
		# min amount out
		expected = Decimal(8000000)/Decimal(1e18)
		assert expectEqualWithError(result, expected)

	def test_out_given_in_extreme_weights(weightedmath_test):
		# Max weights relation
		# Weight relation = 130.07
		token_balance_in = Decimal(100)
		token_weight_in = Decimal(130.7)
		token_balance_out = Decimal(100)
		token_weight_out = Decimal(1)
		token_amount_out = Decimal(15)
		result = WeightedMath.calc_out_given_in(token_balance_in, token_weight_in, token_balance_out, token_weight_out, token_amount_out)

		assert isinstance(result, Decimal)

		#Test out given in 
		expected = Decimal(9999999883374836452)/Decimal(1e17)
		assert expectEqualWithError(result, expected)

	def test_in_given_out_extreme_weights(weightedmath_test):
		# Min weights relation
		# Weight relation = 0.00769
		token_balance_in = Decimal(100)
		token_weight_in = Decimal(0.00769)
		token_balance_out = Decimal(100)
		token_weight_out = Decimal(1)
		token_amount_out = Decimal(15)
		result = WeightedMath.calc_out_given_in(token_balance_in, token_weight_in, token_balance_out, token_weight_out, token_amount_out)

		assert isinstance(result, Decimal)

		#Test out given in 
		expected = Decimal(0.107419197916188066)
		assert expectEqualWithError(result, expected)


	
	def test_calc_due_token_protocol_swap_fee_amount_two_tokens(weightedmath_test):
		# Returns protocl swap fees
		normalized_weights = [Decimal(0.3), Decimal(0.7)]
		balances = [Decimal(10), Decimal(11)]
		last_invariant = Decimal(10)
		token_index = 1
		current_invariant = Decimal(10.689930449163329926)
		protocol_swap_fee_percentage = Decimal(0.1)
		result = WeightedMath.calc_due_token_protocol_swap_fee_amount(balances[token_index], normalized_weights[token_index], last_invariant, current_invariant, protocol_swap_fee_percentage)
		assert isinstance(result, Decimal)
		expected = Decimal(0.099999999999999999933)
		assert expectEqualWithError(result,expected)

		# With large accumulated fees, caps the invariant growth
		normalized_weights = [Decimal(0.3), Decimal(0.7)]
		balances = [Decimal(10), Decimal(11)]
		token_index = 1
		current_invariant = Decimal(10.689930449163329926)
		last_invariant = current_invariant/Decimal(2)
		protocol_swap_fee_percentage = Decimal(0.1)
		result = WeightedMath.calc_due_token_protocol_swap_fee_amount(balances[token_index], normalized_weights[token_index], last_invariant, current_invariant, protocol_swap_fee_percentage)
		
		assert isinstance(result, Decimal)
		expected = Decimal(0.439148057504926669190)
		assert expectEqualWithError(result,expected)
	
	def test_calc_due_token_protocol_swap_fee_amount_three_tokens(weightedmath_test):
		normalized_weights = [Decimal(0.3), Decimal(0.2), Decimal(0.5)]
		balances = [Decimal(10), Decimal(11), Decimal(12)]
		last_invariant = Decimal(10)

		token_index = 2
		current_invariant = Decimal(11.1652682095187556376)
		
		protocol_swap_fee_percentage = Decimal(0.1)
		result = WeightedMath.calc_due_token_protocol_swap_fee_amount(balances[token_index], normalized_weights[token_index], last_invariant, current_invariant, protocol_swap_fee_percentage)
		
		assert isinstance(result, Decimal)
		expected = Decimal(0.23740649734383223657)
		assert expectEqualWithError(result,expected)



	def test_calc_bpt_out_given_exact_tokens_in(weightedmath_test):
		#Test instance of Decimal
		balances = [Decimal(10), Decimal(12), Decimal(14)]
		normalized_weights = [Decimal(10), Decimal(12), Decimal(14)]
		amounts_in = [Decimal(10), Decimal(12), Decimal(14)]
		bpt_total_supply = Decimal(1)
		swap_fee = Decimal(1)
		result = WeightedMath.calc_bpt_out_given_exact_tokens_in(balances, normalized_weights, amounts_in, bpt_total_supply, swap_fee)
		assert isinstance(result, Decimal)

	def test_calc_token_in_given_exact_bpt_out(weightedmath_test):
		#Test instance of Decimal
		balance = Decimal(1)
		normalized_weight = Decimal(10)
		bpt_amount_out = Decimal(10)
		bpt_total_supply = Decimal(10)
		swap_fee = Decimal(10)
		result = WeightedMath.calc_token_in_given_exact_bpt_out(balance, normalized_weight, bpt_amount_out, bpt_total_supply, swap_fee)
		assert isinstance(result, Decimal)

	def test_calc_bpt_in_given_exact_tokens_out(weightedmath_test):
		#Test instance of Decimal
		balances = [Decimal(10), Decimal(12), Decimal(14)]
		normalized_weights = [Decimal(10), Decimal(12), Decimal(14)]
		bpt_amount_out = [Decimal(10), Decimal(12), Decimal(14)]
		bpt_total_supply = Decimal(1)
		swap_fee = Decimal(1)
		result = WeightedMath.calc_bpt_in_given_exact_tokens_out(balances, normalized_weights, bpt_amount_out, bpt_total_supply, swap_fee)
		assert isinstance(result, Decimal)

	def test_calc_token_out_given_exact_bpt_in(weightedmath_test):
		#Test instance of Decimal
		balance = Decimal(10)
		normalized_weight = Decimal(10)
		bpt_amount_in = Decimal(2)
		bpt_total_supply = Decimal(10)
		swap_fee = Decimal(0)
		result = WeightedMath.calc_token_out_given_exact_bpt_in(balance, normalized_weight, bpt_amount_in, bpt_total_supply, swap_fee)
		assert isinstance(result, Decimal)

	def test_calc_tokens_out_given_exact_bpt_in(weightedmath_test):
		#Test instance of Decimal
		balance = Decimal(10)
		normalized_weight = Decimal(1)
		bpt_amount_in = Decimal(2)
		bpt_total_supply = Decimal(1)
		swap_fee = Decimal(1)
		result = WeightedMath.calc_token_out_given_exact_bpt_in(balance, normalized_weight, bpt_amount_in, bpt_total_supply, swap_fee )
		assert isinstance(result, Decimal)

	
