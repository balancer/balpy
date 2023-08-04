rm -rf ./balpy/balancer-deployments

# Ensure that balancer-deployments has been initialized
git submodule update --init

# Pull from balancer-deployments
git submodule update --remote

# Generate pool artifacts from pool factory build-info
python3 generateMissingPoolArtifacts.py

# Remove all build-info (unnecessary/large files)
rm -rf ./balpy/balancer-deployments/tasks/*/build-info
rm -rf ./balpy/balancer-deployments/tasks/scripts
rm -rf ./balpy/balancer-deployments/tasks/deprecated/*/build-info

poetry build
