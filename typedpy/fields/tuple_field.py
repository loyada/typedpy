from typedpy.structures import Field, Structure, TypedField, ClassReference
from typedpy.commons import python_ver_atleast_39, wrap_val
from .collections_impl import ContainNestedFieldMixin, _CollectionMeta
from .fields import verify_type_and_uniqueness
from .function_call import Callable


class Tuple(ContainNestedFieldMixin, TypedField, metaclass=_CollectionMeta):
    """
    A tuple field, supports unique items option.
       Expected input is of type `tuple`.

    Arguments:

        unqieItems(`bool`): optional
            are elements required to be unique?

        items(`list`/`tuple` of :class:`Field` or :class:`Structure`): optional
            Describes the fields of the elements.
            Every element in the content is expected to be
            of the corresponding :class:`Field` in items.


    Examples:

    .. code-block:: python

        # a is a tuple of exactly 2 strings that are different from each other.
        a = Tuple(uniqueItems=True, items = [String, String])

        # b is a tuple of 3: string, string and a number up to 10.
        b = Tuple(items = [String, String, Number(maximum=10)])

        # c is a tuple of 3: integer, string, float.
        c = Tuple[Integer, String, Float]

        # The following define a tuple of any number of Integers
        d = Tuple[Integer]

        # It can also contain other structures:
        # Assume we have something like: class Foo(Structure): pass
        # e is a tuple of any number of Integers or Foo instances
        e = Tuple[AnyOf[Integer, Foo]]

        # It can also have arbitrary class
        class MyCustomClass: pass
        Tuple[MyCustomClass]
    """

    _ty = tuple

    def __init__(self, *args, items, uniqueItems=None, **kwargs):
        """
        Constructor
        :param args: pass-through
        :param items: either a single field, which will be enforced for all elements, or a list
         of fields which enforce the elements with the correspondent index
        :param uniqueItems: are elements required to be unique?
        :param kwargs: pass-through
        """
        self.uniqueItems = uniqueItems
        self._serialize = None
        if isinstance(items, (list, tuple)):
            self.items = []
            for item in items:
                if isinstance(item, Field):
                    self.items.append(item)
                elif Field in item.__mro__:
                    self.items.append(item())
                else:
                    raise TypeError("Expected a Field class or instance")
        elif isinstance(items, (Field,)) or Field in items.__mro__:
            self.items = [items]
        else:
            raise TypeError("Expected a list/tuple of Fields or a single Field")
        super().__init__(*args, **kwargs)
        self._set_immutable(getattr(self, "_immutable", False))

    @property
    def get_type(self):
        if self.items and python_ver_atleast_39:
            if not isinstance(self.items, (list, tuple)):
                return tuple[self.items.get_type]
            if len(self.items) == 2:
                return tuple[self.items[0].get_type, self.items[1].get_type]
            if len(self.items) == 3:
                return tuple[
                    self.items[0].get_type,
                    self.items[1].get_type,
                    self.items[2].get_type,
                ]
        return tuple

    def __set__(self, instance, value):
        verify_type_and_uniqueness(tuple, value, self._name, self.uniqueItems)
        if len(self.items) != len(value) and len(self.items) > 1:
            raise ValueError(
                f"{self._name}: Got {wrap_val(value)}; Expected a tuple of length {len(self.items)}"
            )

        temp_st = Structure()
        res = []
        items = self.items if len(self.items) > 1 else self.items * len(value)
        for ind, item in enumerate(items):
            setattr(item, "_name", self._name + f"_{str(ind)}")
            item.__set__(temp_st, value[ind])
            res.append(getattr(temp_st, getattr(item, "_name")))
            res += value[len(items) :]
        value = tuple(res)

        super().__set__(instance, value)

    def serialize(self, value):
        cached: Callable = self._serialize
        if cached is not None:
            return cached(value)
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
                self._serialize = lambda value: [
                    items[i].serialize(x) for (i, x) in enumerate(value)
                ]
                return self._serialize(value)
        return value
