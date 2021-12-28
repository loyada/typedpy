from typedpy.structures import TypedField, _FieldMeta


class _SubClassMeta(_FieldMeta):
    def __getitem__(cls, value):
        return cls(clazz=value)  # pylint: disable=E1120, E1123


class SubClass(TypedField, metaclass=_SubClassMeta):
    """
    A Subclass of an given class

    Arguments:
        clazz(type):
            The class that the field is subclass of

            .. code-block:: python

               class Foo(Structure): pass
               class Bar(Foo): pass

               class Container(Structure):
                   data: dict[SubClass(clazz=Foo), str]

               container = Container(data={Bar: "bar"})
    """

    _ty = type

    def __init__(
        self,
        *args,
        clazz: type,
        **kwargs,
    ):
        if not isinstance(clazz, type):
            raise TypeError("SubClass must accept a class type as argument")
        self._clazz = clazz
        super().__init__(*args, **kwargs)

    def _validate(self, value):
        if not issubclass(value, self._clazz):
            raise TypeError(
                f"{self._name}: Expected a subclass of {self._clazz.__name__}; Got {value}"
            )

    def __set__(self, instance, value):
        if not getattr(instance, "_skip_validation", False):
            self._validate(value)
        super().__set__(instance, value)
