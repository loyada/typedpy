from typedpy.commons import wrap_val
from typedpy.structures import TypedField


class Boolean(TypedField):
    """
    Value of type bool. True or False.
    """

    _ty = bool

    def __set__(self, instance, value):
        mapping = {"True": True, "False": False}
        value = mapping[value] if value in mapping else value
        super().__set__(instance, value)

    def _validate(self, value):
        def err_prefix():
            return f"{self._name}: " if self._name else ""

        if value not in {"True", "False", True, False}:
            raise TypeError(f"{err_prefix()}Expected {self._ty}; Got {wrap_val(value)}")

    def serialize(self, value):
        return value
