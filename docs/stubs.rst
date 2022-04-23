=====================
Creating Python Stubs
=====================

.. currentmodule:: typedpy

.. contents:: :local:


Stub files - Helping the IDE to Resolve Types and Offer Intellisense
====================================================================
(since version 2.15)

Since currently Pycharm does not resolve annotations dynamically, Typedpy offers a way to create a Python Interface file
(pyi file). There are two executables that you get with Typedpy:

1. create-stubs-for-dir - creates stubs for an entire directory recursively:
   Usage:

.. code-block:: bash

    $ create-stubs-for-dir --help
    usage: create-stubs-for-dir [-h] [-s STUBS_DIR] [-x EXCLUDE] src_root_dir directory

    positional arguments:
      src_root_dir          source root directory
      directory             directory to process

    options:
      -h, --help            show this help message and exit
      -s STUBS_DIR, --stubs-dir STUBS_DIR
                            source directory of stubs. Default is .stubs
      -x EXCLUDE, --exclude EXCLUDE
                            exclude patterns in the form path1:path2:path3


This is useful when you start with an existing code base. Note that you can state directories to \
exclude. This is recommended, since there is no reason to include, for example SQLAlchemy ORM models, or other directories
that do not contain any Typedpy classes.

2. process a single python file. This is what you would use on a regular basis, to ensure the stub
   is up-to-date with your code changes (see file-watcher configuration below). Usage:

.. code-block:: bash

    $create_stub.py --help
    usage: create_stub.py [-h] [-s STUBS_DIR] [-x EXCLUDE]
                          src_root_dir src_script_path

    positional arguments:
      src_root_dir          source root directory
      src_script_path       absolute path of python script to process

    options:
      -h, --help            show this help message and exit
      -s STUBS_DIR, --stubs-dir STUBS_DIR
                            source directory of stubs. Default is .stubs
      -x EXCLUDE, --exclude EXCLUDE
                            exclude patterns in the form path1:path2:path3




Note that Python Interface files are ignored during runtime, so if for some reason they are out-of-sync, the only
problem will be that the intellisense will not be up-to-date.



Configuring a File Watcher For Stub Files in Pycharm
----------------------------------------------------
1. Create a directory that will be designated for Python stub files in the project. I use ".stubs".
2. Mark the directory you created as "sources" directory in the "project structure".
3. Set up a new file watcher, with the following configuration:

.. image:: images/Screenshot1.png

4. Optional - You might want to change the scope to ignore certain files, although you can achieve
   the same with the "-x" command line option.


