from setuptools import setup, find_packages
from pathlib import Path

setup(
    name="cec2rs232",
    version="0.1.1",
    author="travis mick",
    author_email="root@lo.calho.st",
    description="Enables a Raspberry Pi to act as a bridge between CEC and RS-232 or IR",
    long_description=(Path(__file__).parent / "README.md").read_text(),
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/tmick0/cec2rs232",
    python_requires='>=3.9',
    install_requires=["pycec", "pyserial", "piir"],
    packages=find_packages(),
    entry_points={
        'console_scripts': ['cec2rs232=cec2rs232.main:main'],
    }
)
