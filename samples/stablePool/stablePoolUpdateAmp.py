import balpy
import time
def main():
	network = "kovan"

	bal = balpy.balpy.balpy(network);
	
	pool_id = "0x6b15a01b5d46a5321b627bd7deef1af57bc629070000000000000000000000d4";
	raw_end_value = 149; 			#MIN_AMP = 1, MAX_AMP = 5000
	duration_in_seconds = 600000; 	#MIN_UPDATE_TIME = 1 day = 86400 seconds
	
	end_time = int(time.time()) + duration_in_seconds;
	bal.balStablePoolStartAmplificationParameterUpdate(pool_id, raw_end_value, end_time, gasEstimateOverride=400000);
		
if __name__ == '__main__':
	main()