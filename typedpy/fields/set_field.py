from typedpy.structures import Structure, ImmutableField

from .collections_impl import SizedCollection, ContainNestedFieldMixin, _CollectionMeta
from .fields import TypedField, _map_to_field
from typedpy.commons import python_ver_atleast_39, wrap_val


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

        if isinstance(self.items, TypedField) and not getattr(
            getattr(self.items, "_ty"), "__hash__"
        ):
            raise TypeError(
                f"Set element of type {getattr(self.items, '_ty')} is not hashable"
            )
        super().__init__(*args, **kwargs)
        self._set_immutable(getattr(self, "_immutable", False))

    @property
    def get_type(self):
        if (
            not isinstance(self.items, (list, tuple))
            and self.items
            and python_ver_atleast_39
        ):
            return set[self.items.get_type]
        return set

    def __set__(self, instance, value):
        cls = self.__class__._ty
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
