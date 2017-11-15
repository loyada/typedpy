import os

from setuptools import setup


with open(os.path.join(os.path.dirname(__file__), "README.rst")) as readme:
    long_description = readme.read()

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache 2",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
]


setup(
    name="typedpy",
    packages=["typedpy", "typedpy.tests"],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    author="Danny Loya",
    author_email="dan.loya@gmail.com",
    classifiers=classifiers,
    description="Typed-safe Python",
    license="Apache 2",
    long_description=long_description,
    url="http://github.com/loyada/typedpy",
    keywords = ['testing', 'type-safe', 'schema', 'validation'],
    version = '0.1'
)

# coverage run --source=typedpy/ setup.py test
# coverage report -m

# pylint - -rcfile = setup.cfg typedpy
#    or
# python3 setup.py lint