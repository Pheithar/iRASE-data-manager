from setuptools import setup, find_packages

setup(
    name="irase-data-manager",
    version="0.0.1",
    author="Alejandro Valverde Mahou",
    author_email="avama@dtu.dk",
    description="A Python library for managing data uploads and downloads on the DTU Data platform for the i-RASE project",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Pheithar/iRASE-data-manager",
    packages=find_packages(),
    install_requires=[],
)
