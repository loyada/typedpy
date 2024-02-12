from typedpy.structures import TypedField, ImmutableField
from .numbers import Number, Positive, Negative, NonPositive, NonNegative


class Float(TypedField, Number):
    """
    An extension of :class:`Number` for a float. Also excepts an int, which will be converted to a float.
    """

    _ty = float

    def __set__(self, instance, value):
        converted = (
            float(value)
            if isinstance(value, int) and value is not True and value is not False
            else value
        )
        super().__set__(instance, converted)

    def _validate(self, value):
        converted = (
            float(value)
            if isinstance(value, int) and value is not True and value is not False
            else value
        )
        super()._validate(converted)
        Number._validate_static(self, converted)


class PositiveFloat(Float, Positive):
    """
    An combination of :class:`Float` and :class:`Positive`
    """

    pass


class NegativeFloat(Float, Negative):
    """
    An combination of :class:`Float` and :class:`Negative`
    """

    pass


class NonPositiveFloat(Float, NonPositive):
    """
    An combination of :class:`Float` and :class:`NonPositive`
    """

    pass


class NonNegativeFloat(Float, NonNegative):
    """
    An combination of :class:`Float` and :class:`NonNegative`
    """

    pass


class ImmutableFloat(ImmutableField, Float):  # pylint: disable=
    """
    An immutable version of :class:`Float`
    """

    pass
