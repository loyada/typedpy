import os

from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme:
    long_description = readme.read()

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

setup(
    name="typedpy",
    packages=find_packages(
        include=[
            "typedpy",
            "typedpy.scripts",
            "typedpy.structures",
            "typedpy.fields",
            "typedpy.extfields",
            "typedpy.json_schema",
            "typedpy.serialization",
            "typedpy.stubs",
        ]
    ),
    entry_points={
        "console_scripts": [
            "create-stub=typedpy.scripts.create_stub:main",
            "create-stubs-for-dir=typedpy.scripts.create_stubs:main",
        ],
    },
    install_requires=[],
    author="Danny Loya",
    author_email="dan.loya@gmail.com",
    classifiers=classifiers,
    description="Type-safe Python",
    long_description_content_type="text/markdown",
    license="MIT",
    long_description=long_description,
    url="http://github.com/loyada/typedpy",
    download_url="https://github.com/loyada/typedpy/archive/v2.28.3.tar.gz",
    keywords=["testing", "type-safe", "strict", "schema", "validation"],
    version="2.28.3",
)

# coverage run --source=typedpy/ setup.py test
# coverage html
# load in browser from coverage_html_report

# pylint --rcfile=setup.cfg typedpy
#    or
# python3 setup.py lint
