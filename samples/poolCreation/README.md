# Pool Creation

* Make a virtual environment
	* python3 -m venv ./venv
	* source ./venv/bin/activate
* Install balpy
	* python3 -m pip install balpy
* Source your environment (balpy will warn you if you forget this step)
* Copy a pool config for the poolType you want to create
	* cp sampleWeightedPool.json mySuperAwesomePool.json
* Edit your new pool file in your favorite text editor
* Run the Python script
	* python3 poolCreationSample.py mySuperAwesomePool.json
