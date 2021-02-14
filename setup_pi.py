"""
This script sets up a library.

Usage:

    library creation...

        python setup.py bdist_wheel

        [stores .whl file in ./dist directory]

            ./dist/whendo-0.0.1-py3-none-any.whl

    library installation with example file...

        pip install /path/to/whendo-0.0.1-py3-none-any.whl

"""
from setuptools import setup, find_packages, find_namespace_packages

# To use a consistent encoding
from codecs import open
import os

# The directory containing this file
HERE = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(HERE, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [
        dirpath
        for dirpath, dirnames, filenames in os.walk(package)
        if os.path.exists(os.path.join(dirpath, "__init__.py"))
    ]

# This call to setup() does all the work
setup(
    name="whendo",
    version="0.0.1",
    description="action scheduling library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/electronhead/whendo",
    author="Gary Beaver",
    author_email="gary.beaver@electronhead.com",
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        # "Programming Language :: Python",
        # "Programming Language :: Python :: 3",
        # "Programming Language :: Python :: 3.6",
        # "Programming Language :: Python :: 3.7",
        # "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent"
    ],
    packages=get_packages('whendo'),
    # packages=find_packages(exclude=['test', 'core', 'api', 'sdk']),
    install_requires=["uvicorn", "fastapi", "pydantic", "schedule", "requests", "netifaces", "Mock.GPIO", "RPi.GPIO"],
    setup_requires=["pytest-runner"],
    tests_require=["pytest", "httpx", "pytest-asyncio", "asyncio"],
    test_suite="test"
)