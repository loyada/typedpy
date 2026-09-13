from collections import OrderedDict

from typedpy.commons import private_copy_of_field
from typedpy.structures import TypedField, Structure, ImmutableField

from .collections_impl import (
    _DictStruct,
    SizedCollection,
    ContainNestedFieldMixin,
    _CollectionMeta,
)
from .fields import _map_to_field


class Map(
    SizedCollection, ContainNestedFieldMixin, TypedField, metaclass=_CollectionMeta
):
    """
    A map/dictionary collection. Accepts input of type `dict`

    Arguments:
        minItems(int): optional
            minimal size
        maxItems(int): optional
            maximal size
        items(tuple of 2 :class:`Field` or :class:`Structure`  elements): optional
            The first element is the Field for keys, the second is for values.
            Examples:

            .. code-block:: python

                age_by_name = Map[String, PositiveInt]
                # Let's assume we defined a Structure "Person"
                person_by_id = Map[String, Person]
                # even Structure reference is supported for keys!
                id_by_person = Map[Person, String]
                id_by_person = Map[Person, String]

    """

    _ty = dict

    def __init__(self, *args, items=None, **kwargs):
        if items is not None and (
            not isinstance(items, (tuple, list)) or len(items) != 2
        ):
            raise TypeError("items is expected to be a list/tuple of two fields")
        if items is None:
            self.items = None
        else:
            self.items = []
            for item in items:
                self.items.append(_map_to_field(item))
            key_field = self.items[0]
            if isinstance(key_field, TypedField) and not getattr(
                getattr(key_field, "_ty"), "__hash__"
            ):
                raise TypeError(
                    f"Key field of type {key_field}, with underlying type of {getattr(key_field, '_ty')} "
                    "is not hashable"
                )
        self._custom_deep_copy_implementation = True
        super().__init__(*args, **kwargs)
        self._set_immutable(getattr(self, "_immutable", False))

    def __set__(self, instance, value):
        if not isinstance(value, dict):
            raise TypeError(f"{self._name}: Expected a dict")
        self.validate_size(value, self._name)

        if self.items is not None:
            # self.items[0]/[1] are shared class-level state (see array.py's
            # extract_field_value); rename private copies instead of them.
            key_field = private_copy_of_field(self.items[0])
            value_field = private_copy_of_field(self.items[1])
            key_name = f"{self._name}_key"
            value_name = f"{self._name}_value"
            setattr(key_field, "_name", key_name)
            setattr(value_field, "_name", value_name)
            res = OrderedDict()
            for key, val in value.items():
                temp_st = Structure()
                key_field.__set__(temp_st, key)
                value_field.__set__(temp_st, val)

                res[getattr(temp_st, key_name)] = getattr(temp_st, value_name)
                value = res

        super().__set__(instance, _DictStruct(self, instance, value, self._name))

    def serialize(self, value):
        if self.items is not None:
            key_field, value_field = self.items[0], self.items[1]
            key_serialize = key_field.serialize
            value_serialize = value_field.serialize
            return {key_serialize(k): value_serialize(v) for k, v in value.items()}
        return value


class ImmutableMap(ImmutableField, Map):
    """
    An immutable version of :class:`Map`
    """

    pass
