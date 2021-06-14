import os

from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme:
    long_description = readme.read()

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
]

setup(
    name="typedpy",
    packages=["typedpy"],
    install_requires=[],
    author="Danny Loya",
    author_email="dan.loya@gmail.com",
    classifiers=classifiers,
    description="Type-safe Python",
    long_description_content_type="text/markdown",
    license="MIT",
    long_description=long_description,
    url="http://github.com/loyada/typedpy",
    download_url ="https://github.com/loyada/typedpy/archive/v2.4.4.tar.gz",
    keywords=['testing', 'type-safe', 'strict', 'schema', 'validation'],
    version='2.4.4'
)

# coverage run --source=typedpy/ setup.py test
# coverage html
# load in browser from coverage_html_report

# pylint --rcfile=setup.cfg typedpy
#    or
# python3 setup.py lint
