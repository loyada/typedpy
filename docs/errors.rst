==================
Well Formed Errors
==================


.. currentmodule:: typedpy

.. contents:: :local:

Basic Usage
===========

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


Failing Fast vs Gathering All the Errors
========================================
By default, the __init__() function of a structure fails fast. However, Typepy provides an option to collect all the
errors and then throw. An example use-case: a webapp, submits a form to a back-end with a typedpy API. The web-app
may want to present all the validation errors in the data, instead of just the first one it encountered.

An example of usage, take from the automated tests:


.. code-block:: python

    @fixture(name="all_errors")
    def fixture_all_errors():
        Structure.set_fail_fast(False)
        yield
        Structure.set_fail_fast(True)


    def test_multiple_errors_not_fail_fast(all_errors):
        with raises(Exception) as ex:
            Foo(a=1, b=1000, c=-5, arr=[1])
        errs = standard_readable_error_for_typedpy_exception(ex.value)
        assert ErrorInfo(field='b', problem='Expected a maximum of 100', value='1000') in errs
        assert ErrorInfo(field='arr_0', problem='Expected a string', value='1') in errs
        assert ErrorInfo(field='c', problem='Expected a positive number', value='-5') in errs

