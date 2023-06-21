from typing import Callable

from typedpy.structures import (
    Field,
    Structure,
    TypedField,
    ImmutableField,
    ClassReference,
)
from typedpy.commons import python_ver_atleast_39
from .collections_impl import (
    _ListStruct,
    SizedCollection,
    ContainNestedFieldMixin,
    _CollectionMeta,
)
from .fields import _map_to_field, verify_type_and_uniqueness
from .numbers import Number
from .strings import String


def extract_field_value(*, self, value, cls):
    setattr(self.items, "_name", self._name)
    res = cls()
    temp_st = Structure()
    for i, val in enumerate(value):
        setattr(self.items, "_name", self._name + f"_{str(i)}")
        self.items.__set__(temp_st, val)  # pylint: disable=unnecessary-dunder-call
        res.append(getattr(temp_st, getattr(self.items, "_name")))
    return res


def init_array_like(
    self, *args, items=None, uniqueItems=None, additionalItems=None, **kwargs
):
    self.uniqueItems = uniqueItems
    self.additionalItems = additionalItems
    if isinstance(items, list):
        self.items = []
        for item in items:
            self.items.append(_map_to_field(item))
    else:
        self.items = _map_to_field(items)


def _get_items(items):
    if isinstance(items, list):
        res = []
        for item in items:
            res.append(_map_to_field(item))
    else:
        res = _map_to_field(items)
    return res


def has_multiple_items(items):
    return not isinstance(items, (list, tuple)) and items and python_ver_atleast_39


class Array(
    SizedCollection,
    ContainNestedFieldMixin,
    TypedField,
    metaclass=_CollectionMeta,
):
    """
    An Array field, similar to a list. Supports the properties in JSON schema draft 4.
    Expected input is of type `list`.

    Arguments:
        minItems(int): optional
            minimal size
        maxItems(int): optional
            maximal size
        unqieItems(bool): optional
            are elements required to be unique?
        additionalItems(bool): optional
            Relevant in case items parameter is a list of Fields. Is it allowed to have additional
            elements beyond the ones defined in "items"?
        items(a :class:`Field` or :class:`Structure`, or a list/tuple of :class:`Field` or :class:`Structure`): optional
            Describes the fields of the elements.
            If a items if a :class:`Field`, then it applies to all items.
            If a items is a list, then every element in the content is expected to be
            of the corresponding field in items.
            Examples:

            .. code-block:: python

                names = Array[String]
                names = Array[String(minLengh=3)]
                names = Array(minItems=5, items=String)
                my_record = Array(items=[String, Integer(minimum=5), String])
                my_lists = Array[Array[Integer]]
                my_structs = Array[StructureReference(a=Integer, b=Float)]
                # Let's say we defined a Structure "Person"
                people = Array[Person]

                # Assume Foo is an arbitrary (non-Typedpy) class
                foos = Array[Foo]

    """

    _ty = list

    # pylint: disable=duplicate-code
    def __init__(  # pylint: disable=duplicate-code
        self, *args, items=None, uniqueItems=None, additionalItems=None, **kwargs
    ):
        """
        Constructor
        :param args: pass-through
        :param items: either a single field, which will be enforced for all elements, or a list
         of fields which enforce the elements with the correspondent index
        :param uniqueItems: are elements required to be unique?
        :param additionalItems: Relevant if "items" is a list. Is it allowed to have additional
        elements beyond the ones defined in "items"?
        :param kwargs: pass-through
        """

        self.uniqueItems = uniqueItems
        self.additionalItems = additionalItems
        self.items = _get_items(items)
        self._serialize = None
        super().__init__(*args, **kwargs)
        self._set_immutable(getattr(self, "_immutable", False))

    @property
    def get_type(self):
        if has_multiple_items(self.items):
            return list[self.items.get_type]
        return list

    def __set__(self, instance, value):
        if getattr(instance, "_trust_supplied_values", False):
            super().__set__(instance, value)
            return
        verify_type_and_uniqueness(list, value, self._name, self.uniqueItems)
        self.validate_size(value, self._name)
        if self.items is not None:
            if isinstance(self.items, Field):
                value = extract_field_value(self=self, value=value, cls=list)
            elif isinstance(self.items, list):
                additional_properties_forbidden = self.additionalItems is False

                if not getattr(instance, "_skip_validation", False):
                    if len(self.items) > len(value) or (
                        additional_properties_forbidden and len(self.items) > len(value)
                    ):
                        raise ValueError(
                            f"{self._name}: Got {value}; Expected an array of length {len(self.items)}"
                        )
                temp_st = Structure()
                temp_st._skip_validation = getattr(instance, "_skip_validation", False)
                res = []
                for ind, item in enumerate(self.items):
                    if ind >= len(value):
                        continue
                    setattr(item, "_name", self._name + f"_{str(ind)}")
                    item.__set__(temp_st, value[ind])
                    res.append(getattr(temp_st, getattr(item, "_name")))
                res += value[len(self.items) :]
                value = res

        super().__set__(instance, _ListStruct(self, instance, value, self._name))

    def _from_trusted_value(self, value, instance):
        if isinstance(value, _ListStruct):
            return _ListStruct(self, instance, value, self._name)
        return value

    def serialize(self, value):
        cached: Callable = getattr(self, "_serialize", None)
        if cached is not None:
            return cached(value)  # pylint: disable=E1102
        items = self.items
        if items is not None:
            if isinstance(items, Field):
                if isinstance(items, Number) or items.__class__ is String:
                    self._serialize = lambda value: value
                    return value
                if isinstance(items, ClassReference):
                    serializer = items._ty.serialize
                    self._serialize = lambda value: [serializer(x) for x in value]
                    return self._serialize(value)
                serialize = items.serialize
                self._serialize = lambda value: [serialize(x) for x in value]
                return self._serialize(value)
            elif isinstance(items, list):
                self._serialize = lambda value: [
                    items[i].serialize(x) for (i, x) in enumerate(value)
                ]
                return self._serialize(value)
        return value


class ImmutableArray(ImmutableField, Array):
    """
    An immutable version of :class:`Array`
    """
