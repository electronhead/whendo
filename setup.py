"""
This script is the minimal script to build distribution files.

setuptools.setup() looks for configuration information in setup.cfg.
"""
import setuptools

setuptools.setup()

"""
Added as a workaround so that...
    >> python setup.py sdist bdist_wheel
...would work on raspberry pi os using a setup.cfg file.
"""
packages = setuptools.find_packages(include=['core', 'api', 'sdk'], exclude=['test'])