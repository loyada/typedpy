from decimal import Decimal, InvalidOperation

from .serializable_field import SerializableField
from .numbers import Number


class DecimalNumber(Number, SerializableField):
    """
    An extension of :class:`Number` for a Decimal. Accepts anything that can be
    converted to a Decimal.
    It converts the value to a Decimal.
    """

    def __set__(self, instance, value):
        try:
            value = Decimal(value)
        except TypeError as ex:
            raise TypeError(f"{self._name}: {ex.args[0]}") from ex
        except InvalidOperation as ex:
            raise ValueError(f"{self._name}: {ex.args[0]}") from ex

        super().__set__(instance, value)

    def serialize(self, value):
        return float(value)

    def deserialize(self, value):
        return Decimal(value)

    @property
    def get_type(self):
        return Decimal
