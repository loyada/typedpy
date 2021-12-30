import enum

from .fields import String
from .structures import Field, _FieldMeta


class _EnumMeta(_FieldMeta):
    def __getitem__(cls, values):
        if isinstance(values, (type,)) and issubclass(values, (enum.Enum,)):
            return cls(values=values)  # pylint: disable=E1120, E1123
        return cls(values=list(values))  # pylint: disable=E1120, E1123


class Enum(Field, metaclass=_EnumMeta):
    """
    Enum field. value can be one of predefined values.

    Arguments:
         values(`list` or `set` or `tuple`, alternatively an enum Type):
             allowed values. Can be of any type.
             Alternatively, can be an enum.Enum type. See example below.
             When defined with an enum.Enum, serialization converts to strings,
             while deserialization expects strings. In this case, strings are converted
             to the original enum values.

    Examples:

    .. code-block:: python

       class Values(enum.Enum):
            ABC = enum.auto()
            DEF = enum.auto()
            GHI = enum.auto()

       class Example(Structure):
          arr = Array[Enum[Values]]
          e = Enum['abc', 'x', 'def', 3]

       example = Example(arr=[Values.ABC, 'DEF'],e=3)
       assert example.arr = [Values.ABC, Values.DEF]

       # deserialization example:
       deserialized = Deserializer(target_class=Example).deserialize({'arr': ['GHI', 'DEF', 'ABC'], 'e': 3})
       assert deserialized.arr == [Values.GHI, Values.DEF, Values.ABC]
    """

    def __init__(self, *args, values, **kwargs):
        self._is_enum = isinstance(values, (type,)) and issubclass(values, enum.Enum)
        if self._is_enum:
            self._enum_class = values
            self.values = list(values)
        else:
            self.values = values
        super().__init__(*args, **kwargs)

    def _validate(self, value):
        if self._is_enum:
            enum_names = {v.name for v in self._enum_class}
            if value not in enum_names and not isinstance(value, (self._enum_class,)):
                enum_values = [r.name for r in self._enum_class]
                if len(enum_values) < 11:
                    raise ValueError(
                        f"{self._name}: Got {value}; Expected one of: {', '.join(enum_values)}"
                    )
                raise ValueError(
                    f"{self._name}: Got {value}; Expected a value of {self._enum_class}"
                )

        elif value not in self.values:
            raise ValueError(
                f"{self._name}: Got {value}; Expected one of {', '.join([str(v) for v in self.values])}"
            )

    def deserialize(self, value):  # pylint: disable=no-self-use
        if self._is_enum and isinstance(value, (str,)):
                return self._enum_class[value]
        return value

    def __set__(self, instance, value):
        self._validate(value)
        if self._is_enum:
            if isinstance(value, (str,)):
                value = self._enum_class[value]
        super().__set__(instance, value)


class EnumString(Enum, String):
    """
    Combination of :class:`Enum` and :class:`String`. This is useful if you want to further
    limit your allowable enum values, using :class:`String` attributes, such as pattern, maxLength.

    Example:

    .. code-block:: python

        predefined_list = ['abc', 'x', 'def', 'yy']

        EnumString(values=predefined_list, minLength=3)

    """

    pass


