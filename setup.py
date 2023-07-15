from setuptools import setup, find_packages

setup(
	name="pfhm",
	version="0.0.1",
	license="LICENSE",
    install_requires=["numpy"],
	packages=find_packages(include=['pfhm'])
)