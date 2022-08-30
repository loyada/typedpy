from typedpy_libs.structures import Field


class SerializableField(Field):
    """
    An abstract class for a field that has custom serialization or deserialization.
    can override the method.

    .. code-block:: python

      serialize(self, value),
      deserialize(self, value)

    These methods are not being used for pickling.
    """

    def serialize(self, value):
        return value

    def deserialize(self, value):
        return value
