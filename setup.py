from setuptools import setup, find_packages
import sys

if sys.version_info < (3, 0, 6):
    sys.exit('Package requires python3.6')

setup(
    name="tweet_collector",
    version="0.1.0",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        'pymongo'
    ]
)
