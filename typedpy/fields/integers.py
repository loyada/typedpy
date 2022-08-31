from typedpy.structures import TypedField, ImmutableField

from .numbers import Number, Positive, Negative, NonPositive, NonNegative


class Integer(TypedField, Number):
    """
    An extension of :class:`Number` for an integer. Accepts int
    """

    _ty = int

    def _validate(self, value):
        super()._validate(value)
        Number._validate_static(self, value)


class PositiveInt(Integer, Positive):
    """
    An combination of :class:`Integer` and :class:`Positive`
    """

    pass


class NegativeInt(Integer, Negative):
    """
    An combination of :class:`Integer` and :class:`Negative`
    """

    pass


class NonPositiveInt(Integer, NonPositive):
    """
    An combination of :class:`Integer` and :class:`NonPositive`
    """

    pass


class NonNegativeInt(Integer, NonNegative):
    """
    An combination of :class:`Integer` and :class:`NonNegative`
    """

    pass


class ImmutableInteger(ImmutableField, Integer):
    """
    An immutable version of :class:`Integer`
    """

    pass
