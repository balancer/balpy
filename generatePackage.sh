# Ensure that balancer-deployments has been initialized
git submodule update --init

# Pull from balancer-deployments
git submodule update --remote

# Remove all build-info (unnecessary/large files)
rm -rf ./balpy/balancer-deployments/tasks/*/build-info
rm -rf ./balpy/balancer-deployments/tasks/{deprecated,scripts}

poetry build
