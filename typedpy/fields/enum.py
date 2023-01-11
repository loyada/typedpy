import enum
from typing import Any

from typedpy.commons import first_in, wrap_val
from typedpy.structures import FieldMeta
from .strings import String
from .serializable_field import SerializableField


class _EnumMeta(FieldMeta):
    def __getitem__(cls, values):
        if isinstance(values, (type,)) and issubclass(values, (enum.Enum,)):
            return cls(values=values)  # pylint: disable=E1120, E1123
        return cls(values=list(values))  # pylint: disable=E1120, E1123


def _all_values_from_single_enum(values):
    clazz = first_in(values).__class__
    if not (isinstance(clazz, (type,)) and issubclass(clazz, enum.Enum)):
        return False
    return all(v.__class__ is clazz for v in values)


class Enum(SerializableField, metaclass=_EnumMeta):
    """
    Enum field. value can be one of predefined values.

    Arguments:
         values(`list` or `set` or `tuple`, alternatively an enum Type):
             allowed values. Can be of any type.
             Alternatively, can be an enum.Enum type. See example below.
             When defined with an enum.Enum, serialization converts to strings,
             while deserialization expects strings (unless using serialization_by_value).
             In this case, strings are converted to the original enum values.

             Another option is assign a list of specific values from an enum.Enum class.
             In this case, it will work like asigning an Enum class, but allowing only specific values
             of that enum (see example below).

         serialization_by_value(bool): optional
             When set to True and the values is an enum.Enum class, then instead of serializing
             by the name of the enum, serialize by its value, and similarly, when deserializing,
             expect the enum value instead of the name. Default is False.
             This is especially useful when you are interfacing with another system and the values
              are strings that you don't control, like the example below.



    Examples:

    .. code-block:: python

       class Values(enum.Enum):
            ABC = 1
            DEF = 2
            GHI = 3

       class Example(Structure):
          arr = Array[Enum[Values]]
          e = Enum['abc', 'x', 'def', 3]

       example = Example(arr=[Values.ABC, 'DEF'],e=3)
       assert example.arr = [Values.ABC, Values.DEF]

       # deserialization example:
       deserialized = Deserializer(target_class=Example).deserialize({'arr': ['GHI', 'DEF', 'ABC'], 'e': 3})
       assert deserialized.arr == [Values.GHI, Values.DEF, Values.ABC]


    An example of serialization_by_value:

     .. code-block:: python

        class StreamCommand(enum.Enum):
            open = "open new stream"
            close = "close current stream"
            delete = "delete steam"

        class Action(Structure):
            command: Enum(values=StreamCommand, serialization_by_value=True)
            ....


        assert Deserializer(Action).deserialize({"command": "delete stream"}).command is StreamCommand.delete

    An example of allowing only specific values of an Enum class, referencging StreamCommand in the previous example:

    .. code-block:: python

       class Action(Structure):
            command: Enum(values=[StreamCommand.open, StreamCommand.close], serialization_by_value=True)
            ....

      # command works like in the previous example, but allows open/close values from StreamCommand, thus
      # the following line results in an exception:
      Deserializer(Action).deserialize({"command": "delete stream"})

    """

    def __init__(self, *args, values, serialization_by_value: bool = False, **kwargs):
        if not values:
            raise ValueError("Enum requires values parameters")
        self._is_enum = (
            issubclass(values, enum.Enum)
            if isinstance(values, (type,))
            else _all_values_from_single_enum(values)
        )
        self.serialization_by_value = serialization_by_value

        if self._is_enum:
            self._enum_class = (
                values if isinstance(values, (type,)) else first_in(values).__class__
            )
            if serialization_by_value:
                self._enum_by_value = {e.value: e for e in self._enum_class}
            self._valid_enum_values = (
                list(self._enum_class) if isinstance(values, (type,)) else values
            )
            self.values = list(values)
        else:
            self.values = values
        super().__init__(*args, **kwargs)

    def _validate(self, value):
        if self._is_enum:
            enum_names = {v.name for v in self._valid_enum_values}
            if value not in enum_names and value not in self._valid_enum_values:
                enum_values = [r.name for r in self._valid_enum_values]
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

    def serialize(self, value):
        if self._is_enum:
            if self.serialization_by_value:
                if not isinstance(value.value, (bool, str, int, float)):
                    raise TypeError(
                        f"{self._name}: Cannot serialize value: {value.value}"
                    )
            return value.value if self.serialization_by_value else value.name
        return value

    def deserialize(self, value):
        if self._is_enum:
            if self.serialization_by_value:
                if value not in self._enum_by_value:
                    raise ValueError(f"Invalid value: {wrap_val(value)}")
                return self._enum_by_value[value]
            if isinstance(value, (str,)):
                valid_names = {v.name for v in self._valid_enum_values}
                if value not in valid_names:
                    raise ValueError(f"Invalid value: {wrap_val(value)}")
                return self._enum_class[value]

        self._validate(value)
        return value

    def __set__(self, instance, value):
        self._validate(value)
        if self._is_enum:
            if isinstance(value, (str,)):
                value = self._enum_class[value]
        super().__set__(instance, value)

    @property
    def get_type(self):
        if self._enum_class:
            return self._enum_class
        return Any


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
