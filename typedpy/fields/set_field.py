from typing import Callable

from typedpy.structures import Structure, ImmutableField, Field, ClassReference
from typedpy.commons import wrap_val
from .array import has_multiple_items

from .collections_impl import SizedCollection, ContainNestedFieldMixin, _CollectionMeta
from .fields import TypedField, _map_to_field


class Set(
    SizedCollection, ContainNestedFieldMixin, TypedField, metaclass=_CollectionMeta
):
    """
    A set collection. Accepts input of type `set`

    Arguments:
        minItems(int): optional
            minimal size
        maxItems(int): optional
            maximal size
        items(:class:`Field` or :class:`Structure`): optional
            The type of the content, can be a predefined :class:`Structure`,
            :class:`Field` or an arbitrary class. In case of an arbitrary
            class, an implicit Field class will be created for it behind the
            scenes. Always prefer an Explicit Typedpy  :class:`Structure` or
            :class:`Field`  if you can.

    Examples:

    .. code-block:: python

        Set[String]
        Set(items=Integer(maximum=10), maxItems = 10)

        # let's assume we defined a Structure 'Person', then we can use it too:
        Set[Person]


    """

    _ty = set

    def __init__(self, *args, items=None, **kwargs):
        self.items = _map_to_field(items)
        self._serialize = None
        if isinstance(self.items, TypedField) and not getattr(
            getattr(self.items, "_ty"), "__hash__"
        ):
            raise TypeError(
                f"Set element of type {getattr(self.items, '_ty')} is not hashable"
            )
        super().__init__(*args, **kwargs)
        self._set_immutable(getattr(self, "_immutable", False))

    def _validate(self, value):
        if isinstance(value, frozenset):
            return

        super()._validate(value)



    @property
    def get_type(self):
        if has_multiple_items(self.items):
            return set[self.items.get_type]
        return set

    def __set__(self, instance, value):
        if getattr(instance, "_trust_supplied_values", False):
            super().__set__(instance, value)
            return
        cls = frozenset if isinstance(value, frozenset) else set
        if not isinstance(value, cls):
            raise TypeError(f"{self._name}: Got {wrap_val(value)}; Expected {cls}")
        self.validate_size(value, self._name)
        if self.items is not None:
            setattr(self.items, "_name", self._name)
            res = []
            for val in value:
                temp_st = Structure()
                self.items.__set__(temp_st, val)
                res.append(getattr(temp_st, getattr(self.items, "_name")))
            value = cls(res)
        super().__set__(instance, value)

    def serialize(self, value):
        cached: Callable = getattr(self, "_serialize", None)
        if cached is not None:
            return cached(value)  # pylint: disable=E1102

        items = self.items
        if items is not None:
            if isinstance(items, Field):
                if isinstance(items, ClassReference):
                    serializer = items._ty.serialize
                    self._serialize = lambda value: [serializer(x) for x in value]
                    return self._serialize(value)
                serialize = items.serialize
                self._serialize = lambda value: [serialize(x) for x in value]
                return self._serialize(value)
            elif isinstance(items, list):
                return [items[i].serialize(x) for (i, x) in enumerate(value)]

        return list(value)


class ImmutableSet(Set, ImmutableField):
    """
    An immutable  :class:`Set`. Internally implemented by a Python frozenset, so it does not have
    any mutation methods. This makes it more developer-friendly.
    """

    _ty = frozenset

    def __set__(self, instance, value):
        if not isinstance(value, (set, frozenset)):
            raise TypeError(f"{self._name}: Got {wrap_val(value)}; Expected {set}")
        self.validate_size(value, self._name)
        if self.items is not None:
            temp_st = Structure()
            setattr(self.items, "_name", self._name)
            res = set()
            for val in value:
                if getattr(self, "_immutable", False):
                    temp_st = Structure()
                self.items.__set__(temp_st, val)
                res.add(getattr(temp_st, getattr(self.items, "_name")))
                value = res
        corrected_value = value if isinstance(value, frozenset) else frozenset(value)
        super().__set__(instance, corrected_value)
