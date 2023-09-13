from setuptools import setup, find_packages

setup(
	name="pfhm",
	version="0.2",
	license="LICENSE",
    install_requires=["numpy"],
	packages=find_packages(include=['pfhm']),
	long_description=open('README.md').read(),
	url='https://github.com/OllieBoyne/pfhm'
)