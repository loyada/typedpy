from typedpy.commons import wrap_val
from .fields import Field


class Sized(Field):
    """
    The length of the value is limited to be at most the maximum given.
    The value can be any iterable.

        Arguments:

            maxlen(`int`):
                maximum length

    """

    def __init__(self, *args, maxlen, **kwargs):
        self.maxlen = maxlen
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if len(value) > self.maxlen:
            raise ValueError(
                f"{self._name}: Got {wrap_val(value)}; Expected a length up to {self.maxlen}"
            )
        super().__set__(instance, value)
