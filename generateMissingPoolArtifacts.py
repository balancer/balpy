import os
import json

def main():

	# Traverse all deprecated tasks
	deprecated_path = "./balpy/balancer-deployments/tasks/deprecated";
	dir_list = os.listdir(deprecated_path)
	dir_list.sort()

	# Filter for pool factories
	full_paths = [os.path.join(deprecated_path, d) for d in dir_list]
	full_dir_paths = [d for d in full_paths if os.path.isdir(d) and "pool" in d.lower()]

	for p in full_dir_paths:
		print("Traversing", p)
		files = os.listdir(os.path.join(p, "artifact"));

		for f in files:
			if "pool" in f.lower() and "factory" in f.lower():

				# Check to see if there is an artifact for the pool AND the factory
				print("\tFound factory:", f)
				pool_file = "".join(f.split("Factory"));
				print("\tTarget pool file:", pool_file)
				pool_path = os.path.join(p, "artifact", pool_file)
				pool_file_exists = os.path.exists(pool_path)
				print("\tPool file exists:", pool_file_exists)

				# If not pool artifact exists, extract it from the pool factory's build-info
				if not pool_file_exists:
					print("\tAttempting to generate from build-info...")
					build_info_path = os.path.join(p, "build-info", f)

					with open(build_info_path) as x:
						build_info = json.load(x)
						contracts = build_info["output"]["contracts"]
						for k in contracts.keys():
							file_name = k.split("/")[-1];
							pool_name = pool_file.split(".")[0]
							contract_file = pool_name + ".sol"

							if file_name == contract_file:
								abi = contracts[k][pool_name]["abi"]
								print("\tPool ABI exists in build-info!")

								# Save to artifacts
								with open(pool_path, 'w') as pp:
									json.dump(abi, pp)

		print()


if __name__ == '__main__':
	main()