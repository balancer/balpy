"""
Define functions as project "scripts" and run them via the
pyproject.toml
"""
import subprocess as sp
import sys

import balancerv2cad as ks
# from balancerv2cad import PKG_NAME, BASE_DIR


def stub_gen() -> None:
    """
    Generate all function stubs
    for the package
    """
    out_file = f"src/{ks.__package__}-stubs"
    path = str(ks.BASE_DIR / 'src' / f'{ks.__package__}')
    try:
        sp.run(f'stubgen -p {ks.__package__} -o {out_file}',
               check=True,
               shell=True)
        sp.run(f'mypy {path}', check=True, shell=True)
    except sp.CalledProcessError as error:
        print(f'{error}')
        sys.exit(1)


def run_analyzer() -> None:
    """
    Run the mypy static type checking analyzer
    """
    path = str(ks.BASE_DIR / 'src' / f'{ks.__package__}')
    try:
        sp.run(f'mypy {path}', check=True, shell=True)
    except sp.CalledProcessError as error:
        print(f'{error}')
        sys.exit(1)


def run_tests():
    """
    An example function to be used as a python poetry
    script. This can be run issueing the command
    'poetry run tests'
    These functions can be as complicated or as simple as you like
    """
    try:
        sp.run('pytest --capture=tee-sys', check=True, shell=True)
    except sp.CalledProcessError as error:
        print(f"{error}")
        sys.exit(1)
