==================
Well Formed Errors
==================


.. currentmodule:: typedpy

.. contents:: :local:

Usage
=====

In a real-world service, we often want our exception information to be communicated in a well-formed way to the
calling service, so that they can do something useful with it, such as present it on the browser.
For this reason, Typedpy includes an "errors" module that implements such functionality.
Here is an example of usage, taken from the tests (test_errors.py):


.. code-block:: python

    from typedpy import ErrorInfo, standard_readable_error_for_typedpy_exception


    def test_real_world_usage():
        try:
            # Supposed this is inconsistent with the definition of structure Foo
            Foo(a=1, b=10, c=1.1, arr=['abc', 1])
        except Exception as ex:
            assert standard_readable_error_for_typedpy_exception(ex) == \
               ErrorInfo(field='arr_1', problem='Expected a string', value='1')

