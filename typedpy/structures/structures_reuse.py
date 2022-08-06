import typing
from typing import Iterable
from .structures import REQUIRED_FIELDS, StructMeta, Structure, _init_class_dict

T = typing.TypeVar("T")


class PartialMeta(type):
    def __getitem__(
        cls: T, clazz: typing.Union[StructMeta, typing.Tuple[StructMeta, str]]
    ) -> T:
        if not isinstance(clazz, StructMeta):
            if not isinstance(clazz, tuple) or (
                isinstance(clazz, tuple)
                and (
                    len(clazz) != 2
                    or not isinstance(clazz[0], StructMeta)
                    or not isinstance(clazz[1], str)
                )
            ):
                raise TypeError(
                    "Partial must have a Structure class as a parameter, and an optional name for the class"
                )
        clazz, classname = (
            clazz if isinstance(clazz, tuple) else (clazz, f"Partial{clazz.__name__}")
        )

        cls_dict = _init_class_dict(clazz)
        for k, v in clazz.get_all_fields_by_name().items():
            cls_dict[k] = v

        cls_dict[REQUIRED_FIELDS] = []

        new_class = type(classname, (Structure,), cls_dict)

        return new_class


class Partial(metaclass=PartialMeta):
    """
    Define a new Structure class with all the fields of the given class, but all of them are optional.
    For Example:

     .. code-block:: python

         class Foo(ImmutableStructure):
            i: int
            d: dict[str, int] = dict
            s: str
            a: set

         class Bar(Partial[Foo]):
            x: str

    "Bar" has all the fields of Foo as optional, and in addition "x" as required. Note that Bar
    does not extend Foo, but it is a Structure class. It does not copy the serialization mappers.
    It does copy other attributes, such as _ignore_none, but Bar can override any of them.

    Another valid usage:

    .. code-block:: python

        Bar = Partial[Foo]

        bar = Bar(i=5)

        # or if you want to have a consistent class name for troubleshooting:
        Bar = Partial[Foo, "Bar"]

    """

    _required = []


class AllFieldsRequiredMeta(type):
    def __getitem__(
        cls, clazz: typing.Union[StructMeta, typing.Tuple[StructMeta, str]]
    ) -> StructMeta:
        if not isinstance(clazz, StructMeta):
            if not isinstance(clazz, tuple) or (
                isinstance(clazz, tuple)
                and (
                    len(clazz) != 2
                    or not isinstance(clazz[0], StructMeta)
                    or not isinstance(clazz[1], str)
                )
            ):
                raise TypeError(
                    "Partial must have a Structure class as a parameter, and an optional name for the class"
                )
        clazz, classname = (
            clazz
            if isinstance(clazz, tuple)
            else (clazz, f"AllFieldsRequired{clazz.__name__}")
        )

        cls_dict = _init_class_dict(clazz)
        cls_dict[REQUIRED_FIELDS] = []
        for k, v in clazz.get_all_fields_by_name().items():
            cls_dict[k] = v
            if getattr(v, "_default") is None:
                cls_dict[REQUIRED_FIELDS].append(k)

        newclass = type(classname, (Structure,), cls_dict)

        return newclass


class AllFieldsRequired(metaclass=AllFieldsRequiredMeta):
    """
    Define a new Structure class with all the fields of the given class, and all are required (even if they were
    not required in the reference class). The exception is fields that were defined with explicit default value.

    For Example:

     .. code-block:: python

         class Foo(ImmutableStructure):
            i: int
            d: dict[str, int] = dict
            s: str
            a: set

         class Bar(AllFieldsRequired[Foo]):
            x: str

    "Bar" has all the fields of Foo as required with the exception of "d" (since it has a default value), and in
     addition "x" as required.
     Note that Bar does not extend Foo, but it is a Structure class. It does not copy the serialization mappers.
     It does copy other attributes, such as _ignore_none,
     but Bar can override any of them.

    Another valid usage:

    .. code-block:: python

        Bar = AllFieldsRequired[Foo]

        bar = Bar(i=5)

        # or if you want to have a consistent class name for troubleshooting:
        Bar = AllFieldsRequired[Foo, "Bar"]

    """

    _required = []


class ExtendMeta(type):
    def __getitem__(
        cls, clazz: typing.Union[StructMeta, typing.Tuple[StructMeta, str]]
    ):
        if not isinstance(clazz, StructMeta):
            if not isinstance(clazz, tuple) or (
                isinstance(clazz, tuple)
                and (
                    len(clazz) != 2
                    or not isinstance(clazz[0], StructMeta)
                    or not isinstance(clazz[1], str)
                )
            ):
                raise TypeError(
                    "Extend must have a Structure class as a parameter, and an optional name for the class"
                )
        clazz, classname = (
            clazz if isinstance(clazz, tuple) else (clazz, f"Extend{clazz.__name__}")
        )
        cls_dict = _init_class_dict(clazz)
        cls_dict[REQUIRED_FIELDS] = getattr(clazz, REQUIRED_FIELDS, [])
        for k, v in clazz.get_all_fields_by_name().items():
            cls_dict[k] = v

        newclass = type(classname, (Structure,), cls_dict)

        return newclass


class Extend(metaclass=ExtendMeta):
    """
    Define a new Structure class with all the fields of the given class
    For Example:

     .. code-block:: python

         class Foo(ImmutableStructure):
            i: int
            d: dict[str, int] = dict
            s: str
            a: set

         class Bar(Extend[Foo]):
            x: str

    "Bar" has all the fields of Foo, and in addition "x". So the required fields in this case are i, s, a, x
    (since d has a default value).
    Note that Bar does not extend Foo, but it is a Structure class.
    It does not copy the serialization mappers. It does copy other attributes, such as _ignore_none,
    but Bar can override any of them.

    Another valid usage:

    .. code-block:: python

        Bar = Extend[Foo]

        bar = Bar(i=5)

        # or if you want to have a consistent class name for troubleshooting:
        Bar = Partial[Foo, "Bar"]

    """

    pass


class OmitMeta(type):
    def __getitem__(
        cls,
        params: typing.Union[
            typing.Tuple[StructMeta, Iterable[str], str],
            typing.Tuple[StructMeta, Iterable[str]],
        ],
    ):
        if (
            not isinstance(params, tuple)
            or not 1 < len(params) < 4
            or not isinstance(params[0], StructMeta)
        ):
            raise TypeError(
                "Omit accepts the source class name, a list of fields,"
                " and an optional name for the new class it creates"
            )
        clazz, fields, *new_name_maybe = params
        class_name = new_name_maybe[0] if new_name_maybe else f"Omit{clazz.__name__}"
        return clazz.omit(*fields, class_name=class_name)


class Omit(metaclass=OmitMeta):
    """
    Define a new Structure class with all the fields of the given class, except for the omitted ones.
     For Example:

     .. code-block:: python

         class Foo(ImmutableStructure):
            i: int
            d: dict[str, int] = dict
            s: set
            a: str
            b: Integer

         class Bar(Omit[Foo, ("a", "b")]):
            x: int

    "Bar" has the fields: i, d, s, x. Note that Bar does not extend Foo, but it is a Structure class.
    It does not copy the serialization mappers. It does copy other attributes, such as _ignore_none,
    but Bar can override any of them.

    Another valid usage:

    .. code-block:: python

        Bar = Omit[Foo, ("a", "b", "i", "s"), class_name="Bar"]
        bar = Bar(d={"a": 5})

    """

    pass


class PickMeta(type):
    def __getitem__(
        cls,
        params: typing.Union[
            typing.Tuple[StructMeta, Iterable[str], str],
            typing.Tuple[StructMeta, Iterable[str]],
        ],
    ):
        if (
            not isinstance(params, tuple)
            or not 1 < len(params) < 4
            or not isinstance(params[0], StructMeta)
        ):
            raise TypeError(
                "Pick accepts the source class name, a list of fields, and an optional name for the new class it "
                "creates "
            )
        clazz, fields, *new_name_maybe = params
        class_name = new_name_maybe[0] if new_name_maybe else f"Pick{clazz.__name__}"
        return clazz.pick(*fields, class_name=class_name)


class Pick(metaclass=PickMeta):
    """
    Define a new Structure class with that picks specific fields from a predefined class.
     For Example:

     .. code-block:: python

         class Foo(ImmutableStructure):
            i: int
            d: dict[str, int] = dict
            s: set
            a: str
            b: Integer

         class Bar(Pick[Foo, ("a", "b")]):
            x: int

    "Bar" has the fields: a, b, x. Note that Bar does not extend Foo, but it is a Structure class.
     It does not copy the serialization mappers. It does copy other attributes, such as _ignore_none,
    but Bar can override any of them.

    Another valid usage:

    .. code-block:: python

        Bar = Pick[Foo, ("d"), class_name="Bar"]
        bar = Bar(d={"a": 5})

    """

    pass
