from collections import deque

from typedpy.structures import Field, Structure, TypedField, ImmutableField
from .array import _get_items, extract_field_value
from .collections_impl import (
    _DequeStruct,
    SizedCollection,
    ContainNestedFieldMixin,
    _CollectionMeta,
)
from .fields import verify_type_and_uniqueness


class Deque(
    SizedCollection, ContainNestedFieldMixin, TypedField, metaclass=_CollectionMeta
):
    """
    An collections.deque field. Supports the properties in JSON schema draft 4.
    Expected input is of type `collections.deque`.

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

                names = Deque[String]
                names = Deque[String(minLengh=3)]
                names = Deque(minItems=5, items=String)
                my_record = Deque(items=[String, Integer(minimum=5), String])
                my_lists = Deque[Array[Integer]]
                my_structs = Deque[StructureReference(a=Integer, b=Float)]
                # Let's say we defined a Structure "Person"
                people = Deque[Person]

                # Assume Foo is an arbitrary (non-Typedpy) class
                foos = Deque[Foo]

    """

    _ty = deque

    def __init__(
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
        super().__init__(*args, **kwargs)
        self._set_immutable(getattr(self, "_immutable", False))

    def __set__(self, instance, value):
        verify_type_and_uniqueness(deque, value, self._name, self.uniqueItems)
        self.validate_size(value, self._name)
        if self.items is not None:
            if isinstance(self.items, Field):
                value = extract_field_value(self=self, value=value, cls=deque)

            elif isinstance(self.items, list):
                additional_properties_forbidden = self.additionalItems is False

                if not getattr(instance, "_skip_validation", False):
                    if len(self.items) > len(value) or (
                        additional_properties_forbidden and len(self.items) > len(value)
                    ):
                        raise ValueError(
                            f"{self._name}: Got {value}; Expected an deque of length {len(self.items)}"
                        )
                temp_st = Structure()
                temp_st._skip_validation = getattr(instance, "_skip_validation", False)
                res = deque()
                for ind, item in enumerate(self.items):
                    if ind >= len(value):
                        continue
                    setattr(item, "_name", self._name + f"_{str(ind)}")
                    item.__set__(temp_st, value[ind])
                    res.append(getattr(temp_st, getattr(item, "_name")))
                for i in range(len(self.items), len(value)):
                    res.append(value[i])
                value = res

        super().__set__(instance, _DequeStruct(self, instance, value, self._name))

    def serialize(self, value):
        if self.items is not None:
            if isinstance(self.items, Field):
                return [self.items.serialize(x) for x in value]
            elif isinstance(self.items, list):
                return [self.items[i].serialize(x) for (i, x) in enumerate(value)]
        return value


class ImmutableDeque(ImmutableField, Deque):
    """
    An immutable version of :class:`Deque`
    """

    pass
