from setuptools import setup, find_packages
 
setup(
    name='tinyblhost',
    version='0.1',
    packages=find_packages(
        exclude=["tests", "docs", "examples"],
    ),
    install_requires = ['pyserial', 'crcmod']
)