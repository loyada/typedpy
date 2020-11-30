======================
Limitations of Typedpy
======================


.. currentmodule:: typedpy

.. contents:: :local:


Nothing is perfect, and Typedpy as several trade-offs and limitations:

Not supported by IDE
--------------------
| Typedpy is not supported by the IDE code analysis, so there are no warnings/errors that are specific to Typedpy in the IDE.
Errors are found at run-time. There are workaround, like creating a hybrid Structure/dataclass, as explain in :ref:`hybrid` ,
but it is still a limitation.

Not Optimized for Speed
-----------------------
| Typedpy is not optimized for speed, especially when dealing with immutables. If speed is absolutely crucial, you need to be aware of that.


Implicit Arbitrary Class Wrappers
---------------------------------
| Starting with version 2.1, Typedpy supports using arbitrary classes as field types, as described in :ref:`arbitrary-classes`.
| However, if you use the implicit conversion feature in your structure, your data instance cannot be pickled. Typedpy will raise an appropriate exception
if you try to do it, so you will be protected from silent failures.


Type Hints usa can be confusing
-------------------------------
You can't use a Typedpy Field type in type hints, the way you would for a normal type. For example, if we have the
following structure:

.. code-block:: python

    class Example1(Structure):
        names_by_id: Map[String, Array[String]]
        ...


And we have a function get_names_for_id(id, example), the following type hint for the return value is wrong:

.. code-block:: python

    def  get_names_for_id(id: str, example: Example) -> Array[String]:
         ...

The reason is that the field class is not the same as the type of the content. Specifically, Array[String] is not the
same as list[str]. However, if you defined the class as follows:

.. code-block:: python

    class Example1(Structure):
        names_by_id: dict[str, list[str]]
        ...

Typedpy automatically converts it to its own internal field types, and you can use type hints as usual:

.. code-block:: python

    def  get_names_for_id(id: str, example: Example) -> list[str]:
         ...
