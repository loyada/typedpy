from .fields import TypedField
from .serializable_field import SerializableField


class ExceptionField(TypedField, SerializableField):
    """
    As Exception. This is serialized as the string representation of the exception.
    It does not support deserialization.
    """

    _ty = Exception

    def serialize(self, value):
        return value.__class__.__name__
