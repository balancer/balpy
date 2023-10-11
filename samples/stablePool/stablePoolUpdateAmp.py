import time

import balpy


def main():
    network = "kovan"

    bal = balpy.balpy.balpy(network)

    poolId = "0x6b15a01b5d46a5321b627bd7deef1af57bc629070000000000000000000000d4"
    rawEndValue = 149
    # MIN_AMP = 1, MAX_AMP = 5000
    durationInSeconds = 600000
    # MIN_UPDATE_TIME = 1 day = 86400 seconds

    endTime = int(time.time()) + durationInSeconds
    bal.balStablePoolStartAmplificationParameterUpdate(
        poolId, rawEndValue, endTime, gasEstimateOverride=400000
    )


if __name__ == "__main__":
    main()
