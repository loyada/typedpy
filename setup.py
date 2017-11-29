import os

from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), "README.rst")) as readme:
    long_description = readme.read()

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
]

setup(
    name="typedpy",
    packages=["typedpy"],
    setup_requires=['pytest-runner', 'setuptools-lint'],
    tests_require=['pytest', 'coverage', 'pytest-cov'],
    author="Danny Loya",
    author_email="dan.loya@gmail.com",
    classifiers=classifiers,
    description="Type-safe Python",
    license="MIT",
    long_description=long_description,
    url="http://github.com/loyada/typedpy",
    download_url ="https://github.com/loyada/typedpy/archive/v0.2.tar.gz",
    keywords=['testing', 'type-safe', 'strict', 'schema', 'validation'],
    version='0.21'
)

# coverage run --source=typedpy/ setup.py test
# coverage html
# load in browser from coverage_html_report

# pylint --rcfile=setup.cfg typedpy
#    or
# python3 setup.py lint
