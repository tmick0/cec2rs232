from setuptools import setup, find_packages

setup(
    name="cec2rs232",
    version="0.0.1",
    install_requires=["pycec", "pyserial", "piir"],
    packages=find_packages(),
    entry_points={
        'console_scripts': ['cec2rs232=cec2rs232.main:main'],
    }
)
