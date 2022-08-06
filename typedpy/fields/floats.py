from typedpy.structures import TypedField
from .numbers import Number, Positive, Negative, NonPositive, NonNegative
from .. import ImmutableField


class Float(TypedField, Number):
    """
    An extension of :class:`Number` for a float
    """

    _ty = float

    def _validate(self, value):
        super()._validate(value)
        Number._validate_static(self, value)


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
