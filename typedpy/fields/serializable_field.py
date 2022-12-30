from typedpy.structures import Field


class SerializableField(Field):
    """
    An abstract class for a field that has custom deserialization.
    can override the method.

    .. code-block:: python

      deserialize(self, value)

    These methods are not being used for pickling.
    """

    def deserialize(self, value):
        return value
