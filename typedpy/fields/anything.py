from typedpy.structures import Field


class Anything(Field):
    """
    A field that can contain anything (similar to "any" in Typescript).
    Example:

    .. code-block:: python

        class Foo(Structure):
            i = Integer
            some_content = Anything

        # now we can assign anything to some_content property:
        Foo(i=5, some_content = "whatever")
        Foo(i=5, some_content = [1,2,3])
        Foo(i=5, some_content = Bar())

    """

    pass
