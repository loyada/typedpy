import re

from typedpy.commons import wrap_val
from typedpy.structures import TypedField, ImmutableField
from .sized import Sized


class String(TypedField):
    """
    A string value. Accepts input of `str`

    Arguments:
        minLength(int): optional
            minimal length
        maxLength(int): optional
            maximal lengthr
        pattern(str): optional
            string of a regular expression

    """

    _ty = str

    def __init__(self, *args, minLength=None, maxLength=None, pattern=None, **kwargs):
        self.minLength = minLength
        self.maxLength = maxLength
        self.pattern = pattern
        if self.pattern is not None:
            self._compiled_pattern = re.compile(self.pattern)
        super().__init__(*args, **kwargs)

    def _validate(self, value):
        String._validate_static(self, value)

    def _validate_static(self, value):
        def err_prefix():
            return f"{self._name}: Got {wrap_val(value)}; " if self._name else ""

        if not isinstance(value, str):
            raise TypeError(f"{err_prefix()}Expected a string")
        if self.maxLength is not None and len(value) > self.maxLength:
            raise ValueError(
                f"{err_prefix()}Expected a maximum length of {self.maxLength}"
            )
        if self.minLength is not None and len(value) < self.minLength:
            raise ValueError(
                f"{err_prefix()}Expected a minimum length of {self.minLength}"
            )
        if self.pattern is not None and not self._compiled_pattern.match(value):
            raise ValueError(
                f"{err_prefix()}Does not match regular expression: {wrap_val(self.pattern)}"
            )

    def __set__(self, instance, value):
        if getattr(instance, "_trust_supplied_values", False):
            super().__set__(instance, value)
            return
        self._validate(value)
        super().__set__(instance, value)


class SizedString(String, Sized):
    pass


class ImmutableString(ImmutableField, String):
    """
    An immutable version of :class:`String`
    """

    pass
