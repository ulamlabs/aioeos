from setuptools import setup, find_packages

setup(
    name='aioeos',
    version='1.0.0',
    description='Async library for Eosio blockchain, inspired by eospy',
    author='ksiazkowicz',
    author_email='maciej@ulam.io',
    url='https://github.com/ksiazkowicz/aioeos',
    packages=find_packages(),
    test_suite='nose.collector',
    install_requires=[
        'aiohttp>=3.3.1',
        'base58>=1.0.3',
        'ecdsa==0.11'
    ])
