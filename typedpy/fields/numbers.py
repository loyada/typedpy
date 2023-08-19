from decimal import Decimal

from typedpy.structures import ImmutableField, Field
from typedpy.commons import wrap_val


class Number(Field):
    """
    Base class for numerical fields. Based on Json schema draft4.
    Accepts and int or float.

    Arguments:
        multipleOf(int): optional
            The number must be a multiple of this number
        minimum(int or float): optional
            value cannot be lower than this number
        maximum(int or float): optional
            value cannot be higher than this number
        exclusiveMaximum(bool): optional
            marks the maximum threshold above as exclusive

    """

    def __init__(
        self,
        *args,
        multiplesOf=None,
        minimum=None,
        maximum=None,
        exclusiveMaximum=None,
        **kwargs,
    ):
        self.multiplesOf = multiplesOf
        self.minimum = minimum
        self.maximum = maximum
        self.exclusiveMaximum = exclusiveMaximum
        super().__init__(*args, **kwargs)

    def _validate_static(self, value):
        def is_number(val):
            return isinstance(val, (float, int, Decimal))

        def err_prefix():
            return f"{self._name}: Got {wrap_val(value)}; " if self._name else ""

        if not is_number(value):
            raise TypeError(f"{err_prefix()}Expected a number")
        if (
            isinstance(self.multiplesOf, float)
            and int(value / self.multiplesOf) != value / self.multiplesOf
            or isinstance(self.multiplesOf, int)
            and value % self.multiplesOf
        ):
            raise ValueError(
                f"{err_prefix()}Expected a a multiple of {self.multiplesOf}"
            )
        if (is_number(self.minimum)) and self.minimum > value:
            raise ValueError(f"{err_prefix()}Expected a minimum of {self.minimum}")
        if is_number(self.maximum):
            if self.exclusiveMaximum and self.maximum == value:
                raise ValueError(
                    f"{err_prefix()}Expected a maximum of less than {self.maximum}"
                )
            if self.maximum < value:
                raise ValueError(f"{err_prefix()}Expected a maximum of {self.maximum}")

    def _validate(self, value):
        Number._validate_static(self, value)

    def __set__(self, instance, value):
        if not getattr(instance, "_skip_validation", False) and not getattr(
            instance, "_trust_supplied_values", False
        ):
            self._validate(value)
        super().__set__(instance, value)


class Positive(Number):
    """
    An extension of :class:`Number`. Requires the number to be positive
    """

    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError(f"{self._name}: Got {value}; Expected a positive number")
        super().__set__(instance, value)


class NonPositive(Number):
    """
    An extension of :class:`Number`. Requires the number to be negative or 0
    """

    def __set__(self, instance, value):
        if value > 0:
            raise ValueError(
                f"{self._name}: Got {value}; Expected a negative number or 0"
            )
        super().__set__(instance, value)


class Negative(Number):
    """
    An extension of :class:`Number`. Requires the number to be negative
    """

    def __set__(self, instance, value):
        if value >= 0:
            raise ValueError(f"{self._name}: Got {value}; Expected a negative number")
        super().__set__(instance, value)


class NonNegative(Number):
    """
    An extension of :class:`Number`. Requires the number to be positive or 0
    """

    def __set__(self, instance, value):
        if value < 0:
            raise ValueError(
                f"{self._name}: Got {value}; Expected a positive number or 0"
            )
        super().__set__(instance, value)


class ImmutableNumber(ImmutableField, Number):
    """
    An immutable version of :class:`Number`
    """

    pass
