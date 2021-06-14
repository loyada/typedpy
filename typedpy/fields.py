"""
Definitions of various types of fields. Supports JSON draft4 types.
"""
import enum
import re
from collections import OrderedDict, deque
from collections.abc import Iterable

from copy import deepcopy
from functools import reduce
from decimal import Decimal, InvalidOperation

from .commons import wrap_val
from .structures import (
    Field,
    Structure,
    TypedField,
    ClassReference,
    StructMeta,
    ImmutableMixin,
    _FieldMeta,
    NoneField,
    ImmutableField,
)


class SerializableField(Field):
    """
    An abstract class for a field that has custom serialization or deserialization.
    can override the method:
      serialize(self, value),
      deserialize(self, value)

    These methods are not being used for pickling.
    """

    def serialize(self, value):  # pylint: disable=no-self-use
        return value

    def deserialize(self, value):  # pylint: disable=no-self-use
        return value


def _map_to_field(item):
    item = item[0] if isinstance(item, (list, tuple)) and len(item) == 1 else item
    if isinstance(item, StructMeta) and not isinstance(item, Field):
        return ClassReference(item)
    if item in [None, ""] or isinstance(item, Field):
        return item
    elif Field in getattr(item, "__mro__", []):
        return item()
    else:
        raise TypeError("Expected a Field/Structure class or Field instance")


class StructureReference(Field):
    """
    A Field that is an embedded structure within other structure. Allows to create hierarchy.
    This is useful if you want to inline your Structure, as opposed to create an explicit
    class for it.
    All the arguments are passed as attributes of the structure. Example:

    .. code-block:: python

        StructureReference(
            _additionalProperties = False,
            id = String,
            name = String
            age = AnyOf[PositiveInt, PositiveFloat]
        )


    Important: Since Typedpy dynamically creates an internal class for it, this
    field cannot be pickled!
    """

    counter = 0

    def __init__(self, **kwargs):
        classname = "StructureReference_" + str(StructureReference.counter)
        StructureReference.counter += 1

        self._newclass = type(classname, (Structure,), kwargs)
        super().__init__(kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, (dict, Structure)):
            raise TypeError(
                "{}: Expected a dictionary or Structure; got {}".format(
                    self._name, value
                )
            )
        extracted_values = (
            {k: v for (k, v) in value.__dict__.items() if k != "_instantiated"}
            if isinstance(value, (Structure,))
            else value
        )
        newval = self._newclass(**extracted_values)
        super().__set__(instance, newval)

    def __serialize__(self, value):
        raise TypeError("{}: StructuredReference Cannot be pickled".format(self._name))

    def __str__(self):
        props = []
        for k, val in sorted(self._newclass.__dict__.items()):
            if val is not None and not k.startswith("_"):
                props.append("{} = {}".format(k, str(val)))

        propst = ". Properties: {}".format(", ".join(props)) if props else ""
        return "<Structure{}>".format(propst)


class Number(Field):
    """
    Base class for numerical fields. Based on Json schema draft4.
    Accepts and int or float.

    Arguments:
        multipleOf(int): optional
            The number must be a multiple of this number
        minimum(int or float): optional
            value cannot be lower than this number
        maximum(int or float): optional
            value cannot be higher than this number
        exclusiveMaximum(bool): optional
            marks the maximum threshold above as exclusive

    """

    def __init__(
        self,
        *args,
        multiplesOf=None,
        minimum=None,
        maximum=None,
        exclusiveMaximum=None,
        **kwargs
    ):
        self.multiplesOf = multiplesOf
        self.minimum = minimum
        self.maximum = maximum
        self.exclusiveMaximum = exclusiveMaximum
        super().__init__(*args, **kwargs)

    def _validate_static(self, value):
        def is_number(val):
            return isinstance(val, (float, int, Decimal))

        def err_prefix():
            return (
                "{}: Got {}; ".format(self._name, wrap_val(value)) if self._name else ""
            )

        if not is_number(value):
            raise TypeError("{}Expected a number".format(err_prefix()))
        if (
            isinstance(self.multiplesOf, float)
            and int(value / self.multiplesOf) != value / self.multiplesOf
            or isinstance(self.multiplesOf, int)
            and value % self.multiplesOf
        ):
            raise ValueError(
                "{}Expected a a multiple of {}".format(err_prefix(), self.multiplesOf)
            )
        if (is_number(self.minimum)) and self.minimum > value:
            raise ValueError(
                "{}Expected a minimum of {}".format(err_prefix(), self.minimum)
            )
        if is_number(self.maximum):
            if self.exclusiveMaximum and self.maximum == value:
                raise ValueError(
                    "{}Expected a maximum of less than {}".format(
                        err_prefix(), self.maximum
                    )
                )
            if self.maximum < value:
                raise ValueError(
                    "{}Expected a maximum of {}".format(err_prefix(), self.maximum)
                )

    def _validate(self, value):
        Number._validate_static(self, value)

    def __set__(self, instance, value):
        if not getattr(instance, "_skip_validation", False):
            self._validate(value)
        super().__set__(instance, value)


class Integer(TypedField, Number):
    """
    An extension of :class:`Number` for an integer. Accepts int
    """

    _ty = int

    def _validate(self, value):
        super()._validate(value)
        Number._validate_static(self, value)


class DecimalNumber(Number, SerializableField):
    """
    An extension of :class:`Number` for a Decimal. Accepts anything that can be
     converted to a Decimal.
    It converts the value to a Decimal.
    """

    def __set__(self, instance, value):
        try:
            value = Decimal(value)
        except TypeError as ex:
            raise TypeError("{}: {}".format(self._name, ex.args[0])) from ex
        except InvalidOperation as ex:
            raise ValueError("{}: {}".format(self._name, ex.args[0])) from ex

        super().__set__(instance, value)

    def serialize(self, value):
        return float(value)


class StructureClass(TypedField):
    _ty = StructMeta


class String(TypedField):
    """
    A string value. Accepts input of `str`

    Arguments:
        minLength(int): optional
            minimal length
        maxLength(int): optional
            maximal lengthr
        pattern(str): optional
            string of a regular expression

    """

    _ty = str

    def __init__(self, *args, minLength=None, maxLength=None, pattern=None, **kwargs):
        self.minLength = minLength
        self.maxLength = maxLength
        self.pattern = pattern
        if self.pattern is not None:
            self._compiled_pattern = re.compile(self.pattern)
        super().__init__(*args, **kwargs)

    def _validate(self, value):
        String._validate_static(self, value)

    def _validate_static(self, value):
        def err_prefix():
            return (
                "{}: Got {}; ".format(self._name, wrap_val(value)) if self._name else ""
            )

        if not isinstance(value, str):
            raise TypeError("{}Expected a string".format(err_prefix()))
        if self.maxLength is not None and len(value) > self.maxLength:
            raise ValueError(
                "{}Expected a maximum length of {}".format(err_prefix(), self.maxLength)
            )
        if self.minLength is not None and len(value) < self.minLength:
            raise ValueError(
                "{}Expected a minimum length of {}".format(err_prefix(), self.minLength)
            )
        if self.pattern is not None and not self._compiled_pattern.match(value):
            raise ValueError(
                '{}Does not match regular expression: "{}"'.format(
                    err_prefix(), self.pattern
                )
            )

    def __set__(self, instance, value):
        self._validate(value)
        super().__set__(instance, value)


class Function(Field):
    """
    A function or method. Note that this can't be any callable (it can't be a class,
     for example), but a real function
    """

    _bound_method_type = type(Field().__init__)

    def __set__(self, instance, value):
        def is_function(f):
            return type(f) in {
                type(lambda x: x),
                type(open),
                Function._bound_method_type,
            }

        def err_prefix():
            return (
                "{}: Got {}; ".format(self._name, wrap_val(value)) if self._name else ""
            )

        if not is_function(value):
            raise TypeError("{}Expected a function".format(err_prefix()))
        super().__set__(instance, value)


class Generator(TypedField):
    """
    A Python generator. Not serializable.
    """

    _ty = type(x for x in [])


class Anything(Field):
    """
    A field that can contain anything (similar to "any" in Typescript).
    Example:

    .. code-block:: python

        class Foo(Structure):
            i = Integer
            some_content = Anything

        # now we can assign anything to some_content property:
        Foo(i=5, some_content = "whatever")
        Foo(i=5, some_content = [1,2,3])
        Foo(i=5, some_content = Bar())

    """

    pass


class Float(TypedField, Number):
    """
    An extension of :class:`Number` for a float
    """

    _ty = float

    def _validate(self, value):
        super()._validate(value)
        Number._validate_static(self, value)


class Boolean(TypedField):
    """
    Value of type bool. True or False.
    """

    _ty = bool


class Positive(Number):
    """
    An extension of :class:`Number`. Requires the number to be positive
    """

    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError(
                "{}: Got {}; Expected a positive number".format(self._name, value)
            )
        super().__set__(instance, value)


class PositiveFloat(Float, Positive):
    """
    An combination of :class:`Float` and :class:`Positive`
    """

    pass


class PositiveInt(Integer, Positive):
    """
    An combination of :class:`Integer` and :class:`Positive`
    """

    pass


class _IteratorProxyMixin:
    class ListIteratorProxy:
        def __init__(self, the_list):
            self.the_list = the_list
            self.index = 0

        def __next__(self):
            if len(self.the_list) > self.index:
                self.index += 1
                return self.the_list[self.index - 1]
            raise StopIteration


class _ListStruct(list, ImmutableMixin, _IteratorProxyMixin):
    """
    This is a useful wrapper for the content of list in an Array field.
    It ensures that an update of the form:
     mystruct.my_array[i] = new_val
    Will not bypass the validation of the Array.
    """

    def __init__(self, array: Field, struct_instance: Structure, mylist, name: str):
        self._field_definition = array
        self._instance = struct_instance
        self._name = name
        super().__init__(self._get_defensive_copy_if_needed(mylist))

    def __setitem__(self, key, value):
        self._raise_if_immutable()
        copied = self[:]
        copied.__setitem__(key, value)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)

    def __getitem__(self, item):
        val = super().__getitem__(item)
        return self._get_defensive_copy_if_needed(val)

    def __iter__(self):
        if self._is_immutable():
            return _IteratorProxyMixin.ListIteratorProxy(self)
        return super(_ListStruct, self).__iter__()

    def append(self, value):
        self._raise_if_immutable()
        copied = self[:]
        copied.append(value)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)
        super().append(value)

    def extend(self, value):
        self._raise_if_immutable()
        copied = self[:]
        copied.extend(value)
        if getattr(self, "_instance", None):
            setattr(
                self._instance, getattr(self._field_definition, "_name", None), copied
            )

    def insert(self, index: int, value):
        self._raise_if_immutable()
        copied = self[:]
        copied.insert(index, value)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)

    def remove(self, ind):
        self._raise_if_immutable()
        copied = self[:]
        copied.remove(ind)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)

    def copy(self):
        copied = super(_ListStruct, self).copy()
        return deepcopy(copied) if self._is_immutable() else copied

    def clear(self) -> None:
        self._raise_if_immutable()
        setattr(self._instance, getattr(self._field_definition, "_name", None), [])

    def pop(self, index: int = -1):
        self._raise_if_immutable()
        copied = self[:]
        res = copied.pop(index)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)
        return res

    def __getstate__(self):
        return {
            "the_instance": self._instance,
            "the_array": self._field_definition,
            "the_name": self._name,
            "the_values": self[:],
        }

    def __deepcopy__(self, memo={}):
        vals = [deepcopy(v) for v in self[:]]
        instance_id = id(self._instance)
        return _ListStruct(
            array=deepcopy(self._field_definition),
            struct_instance=memo.get(instance_id, self._instance),
            mylist=vals,
            name=self._name,
        )

    def __setstate__(self, state):
        self._name = state["the_name"]
        self._field_definition = state["the_array"]
        self._instance = state["the_instance"]
        super().__init__(state["the_values"])


class _DequeStruct(deque, ImmutableMixin, _IteratorProxyMixin):
    """
    This is a useful wrapper for the content of list in an Deque field.
    It ensures that an update of the form:
     mystruct.my_array[i] = new_val
    Will not bypass the validation of the Array.
    """

    def __init__(
        self,
        deq: Field = None,
        struct_instance: Structure = None,
        mydeque=None,
        name: str = None,
    ):
        self._field_definition = deq
        self._instance = struct_instance
        self._name = name
        if mydeque is not None:
            super().__init__(self._get_defensive_copy_if_needed(mydeque))

    def __setitem__(self, key, value):
        self._raise_if_immutable()
        copied = deque(self)
        copied[key] = value
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)

    def __getitem__(self, item):
        val = super().__getitem__(item)
        return self._get_defensive_copy_if_needed(val)

    def __iter__(self):
        if self._is_immutable():
            return _ListStruct.ListIteratorProxy(self)
        return super(_DequeStruct, self).__iter__()

    def append(self, value):
        self._raise_if_immutable()
        copied = deque(self)
        copied.append(value)
        if self._field_definition:  # Python 3.6
            setattr(
                self._instance, getattr(self._field_definition, "_name", None), copied
            )
        super().append(value)

    def appendleft(self, value):
        self._raise_if_immutable()
        copied = deque(self)
        copied.appendleft(value)
        if self._field_definition:  # Python 3.6
            setattr(
                self._instance, getattr(self._field_definition, "_name", None), copied
            )
        super().append(value)

    def extend(self, iterable: Iterable):
        self._raise_if_immutable()
        copied = deque(self)
        copied.extend(iterable)
        if getattr(self, "_instance", None):
            setattr(
                self._instance, getattr(self._field_definition, "_name", None), copied
            )

    def extendleft(self, iterable: Iterable):
        self._raise_if_immutable()
        copied = deque(self)
        copied.extendleft(iterable)
        if getattr(self, "_instance", None):
            setattr(
                self._instance, getattr(self._field_definition, "_name", None), copied
            )

    def insert(self, index: int, value):
        self._raise_if_immutable()
        copied = deque(self)
        copied.insert(index, value)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)

    def remove(self, ind):
        self._raise_if_immutable()
        copied = deque(self)
        copied.remove(ind)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)

    def copy(self):
        copied = deque(self)
        return deepcopy(copied) if self._is_immutable() else copied

    def clear(self) -> None:
        self._raise_if_immutable()
        setattr(self._instance, getattr(self._field_definition, "_name", None), deque())

    def pop(self, *args, **kwargs):
        self._raise_if_immutable()
        copied = deque(self)
        res = copied.pop()
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)
        return res

    def popleft(self):
        self._raise_if_immutable()
        copied = deque(self)
        res = copied.popleft()
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)
        return res

    def rotate(self, n: int) -> None:
        self._raise_if_immutable()
        # no need to validate again
        super().rotate(n)

    def reverse(self) -> None:
        self._raise_if_immutable()
        # no need to validate again
        super().reverse()

    def __getstate__(self):
        return {
            "the_instance": self._instance,
            "field_def": self._field_definition,
            "the_name": self._name,
            "the_values": deque(self),
        }

    def __deepcopy__(self, memo={}):
        vals = [deepcopy(v) for v in self.copy()]
        instance_id = id(self._instance)
        return _DequeStruct(
            deq=deepcopy(self._field_definition),
            struct_instance=memo.get(instance_id, self._instance),
            mydeque=vals,
            name=self._name,
        )

    def __reduce__(self):
        res = super().__reduce__()
        return res[0], res[1], self.__getstate__(), res[3]

    def __setstate__(self, state):
        self._name = state["the_name"]
        self._field_definition = state["field_def"]
        self._instance = state["the_instance"]
        super().__init__(state["the_values"])


class _DictStruct(dict, ImmutableMixin):
    """
    This is a useful wrapper for the content of dict in an Map field.
    It ensures that an update of the form:
     mystruct.my_map[i] = new_val, or
     mystruct.my_map.update(some_dict)

    ...will not bypass the validation of the Map.
    """

    def __init__(self, the_map, struct_instance, mydict, name):
        self._field_definition = the_map
        self._instance = struct_instance
        self._name = name
        super().__init__(mydict)

    def __setitem__(self, key, value):
        super()._raise_if_immutable()
        copied = self.copy()
        copied.__setitem__(key, value)
        if getattr(self, "_instance", None):
            setattr(
                self._instance, getattr(self._field_definition, "_name", None), copied
            )

        super().__setitem__(key, value)

    def __getitem__(self, item):
        val = super().__getitem__(item)
        return self._get_defensive_copy_if_needed(val)

    def copy(self):
        copied = super(_DictStruct, self).copy()
        return deepcopy(copied) if self._is_immutable() else copied

    def __deepcopy__(self, memo={}):
        new_dict = {deepcopy(k): deepcopy(v) for k, v in self.items()}
        instance_id = id(self._instance)
        return _DictStruct(
            the_map=self._field_definition,
            struct_instance=memo.get(instance_id, self._instance),
            mydict=new_dict,
            name=self._name,
        )

    def items(self):
        return ((k, self._get_defensive_copy_if_needed(v)) for k, v in super().items())

    def values(self):
        return (self._get_defensive_copy_if_needed(v) for v in super().values())

    def __delitem__(self, key):
        self._raise_if_immutable()
        copied = self.copy()
        del copied[key]
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)

    def update(self, *args, **kwargs):
        self._raise_if_immutable()
        copied = self.copy()
        res = copied.update(*args, **kwargs)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)
        return res

    def pop(self, k):
        self._raise_if_immutable()
        copied = self.copy()
        res = copied.pop(k)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)
        return res

    def clear(self) -> None:
        self._raise_if_immutable()
        setattr(self._instance, getattr(self._field_definition, "_name", None), {})

    def __getstate__(self):
        return {
            "_instance": self._instance,
            "_map": self._field_definition,
            "mydict": self.copy(),
            "_name": self._name,
        }

    def __setstate__(self, state):
        self._field_definition = state["_map"]
        self._instance = state["_instance"]
        self._name = state["_name"]
        super().__init__(state["mydict"])


class _CollectionMeta(_FieldMeta):
    def __getitem__(cls, item):
        def validate_and_get_field(val):
            return _FieldMeta.__getitem__(cls, val)

        if isinstance(item, tuple):
            items = [validate_and_get_field(it) for it in item]
            return cls(items=items)  # pylint: disable=E1120, E1123
        return cls(items=validate_and_get_field(item))  # pylint: disable=E1120, E1123


class _EnumMeta(_FieldMeta):
    def __getitem__(cls, values):
        if isinstance(values, (type,)) and issubclass(values, (enum.Enum,)):
            return cls(values=values)  # pylint: disable=E1120, E1123
        return cls(values=list(values))  # pylint: disable=E1120, E1123


class _JSONSchemaDraft4ReuseMeta(_FieldMeta):
    def __getitem__(cls, item):
        def validate_and_get_field(val):
            return _FieldMeta.__getitem__(cls, val)

        if isinstance(item, tuple):
            fields = [validate_and_get_field(it) for it in item]
            return cls(fields)  # pylint: disable=E1120, E1123
        return cls([validate_and_get_field(item)])  # pylint: disable=E1120, E1123


class ContainNestedFieldMixin(Field):
    def _set_immutable(self, immutable: bool):
        items = getattr(self, "items", None)
        super()._set_immutable(immutable)
        if isinstance(items, Field):
            items._set_immutable(immutable)
        elif isinstance(items, (list, tuple)):
            for item in items:
                if isinstance(item, Field):
                    item._set_immutable(immutable)


class SizedCollection:
    def __init__(self, *args, minItems=None, maxItems=None, **kwargs):
        self.minItems = minItems
        self.maxItems = maxItems
        super().__init__(*args, **kwargs)

    def validate_size(self, items, name):
        if self.minItems is not None and len(items) < self.minItems:
            raise ValueError(
                "{}: Expected length of at least {}; Got {}".format(
                    name, self.minItems, items
                )
            )
        if self.maxItems is not None and len(items) > self.maxItems:
            raise ValueError(
                "{}: Expected length of at most {}; Got {}".format(
                    name, self.maxItems, items
                )
            )


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
                "Set element of type {} is not hashable".format(
                    getattr(self.items, "_ty")
                )
            )
        super().__init__(*args, **kwargs)
        self._set_immutable(getattr(self, "_immutable", False))

    def __set__(self, instance, value):
        cls = self.__class__._ty
        if not isinstance(value, cls):
            raise TypeError(
                "{}: Got {}; Expected {}".format(self._name, wrap_val(value), cls)
            )
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
                    "Key field of type {}, with underlying type of {} is not hashable".format(
                        key_field, getattr(key_field, "_ty")
                    )
                )
        self._custom_deep_copy_implementation = True
        super().__init__(*args, **kwargs)
        self._set_immutable(getattr(self, "_immutable", False))

    def __set__(self, instance, value):
        if not isinstance(value, dict):
            raise TypeError("%s: Expected %s" % (self._name, dict))
        self.validate_size(value, self._name)

        if self.items is not None:
            key_field, value_field = self.items[0], self.items[1]
            setattr(key_field, "_name", self._name + "_key")
            setattr(value_field, "_name", self._name + "_value")
            res = OrderedDict()

            for key, val in value.items():
                temp_st = Structure()
                key_field.__set__(temp_st, key)
                value_field.__set__(temp_st, val)
                res[getattr(temp_st, getattr(key_field, "_name"))] = getattr(
                    temp_st, getattr(value_field, "_name")
                )
        super().__set__(instance, _DictStruct(self, instance, value, self._name))


class Array(
    SizedCollection, ContainNestedFieldMixin, TypedField, metaclass=_CollectionMeta
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
        if isinstance(items, list):
            self.items = []
            for item in items:
                self.items.append(_map_to_field(item))
        else:
            self.items = _map_to_field(items)
        super().__init__(*args, **kwargs)
        self._set_immutable(getattr(self, "_immutable", False))

    def __set__(self, instance, value):
        verify_type_and_uniqueness(list, value, self._name, self.uniqueItems)
        self.validate_size(value, self._name)
        if self.items is not None:
            if isinstance(self.items, Field):
                setattr(self.items, "_name", self._name)
                res = []
                for i, val in enumerate(value):
                    temp_st = Structure()
                    setattr(self.items, "_name", self._name + "_{}".format(str(i)))
                    self.items.__set__(temp_st, val)
                    res.append(getattr(temp_st, getattr(self.items, "_name")))
                value = res
            elif isinstance(self.items, list):
                additional_properties_forbidden = self.additionalItems is False

                if not getattr(instance, "_skip_validation", False):
                    if len(self.items) > len(value) or (
                        additional_properties_forbidden and len(self.items) > len(value)
                    ):
                        raise ValueError(
                            "{}: Got {}; Expected an array of length {}".format(
                                self._name, value, len(self.items)
                            )
                        )
                temp_st = Structure()
                temp_st._skip_validation = getattr(instance, "_skip_validation", False)
                res = []
                for ind, item in enumerate(self.items):
                    if ind >= len(value):
                        continue
                    setattr(item, "_name", self._name + "_{}".format(str(ind)))
                    item.__set__(temp_st, value[ind])
                    res.append(getattr(temp_st, getattr(item, "_name")))
                res += value[len(self.items) :]
                value = res

        super().__set__(instance, _ListStruct(self, instance, value, self._name))


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
        if isinstance(items, list):
            self.items = []
            for item in items:
                self.items.append(_map_to_field(item))
        else:
            self.items = _map_to_field(items)
        super().__init__(*args, **kwargs)
        self._set_immutable(getattr(self, "_immutable", False))

    def __set__(self, instance, value):
        verify_type_and_uniqueness(deque, value, self._name, self.uniqueItems)
        self.validate_size(value, self._name)
        if self.items is not None:
            if isinstance(self.items, Field):
                setattr(self.items, "_name", self._name)
                res = deque()
                for i, val in enumerate(value):
                    temp_st = Structure()
                    setattr(self.items, "_name", self._name + "_{}".format(str(i)))
                    self.items.__set__(temp_st, val)
                    res.append(getattr(temp_st, getattr(self.items, "_name")))
                value = res
            elif isinstance(self.items, list):
                additional_properties_forbidden = self.additionalItems is False

                if not getattr(instance, "_skip_validation", False):
                    if len(self.items) > len(value) or (
                        additional_properties_forbidden and len(self.items) > len(value)
                    ):
                        raise ValueError(
                            "{}: Got {}; Expected an deque of length {}".format(
                                self._name, value, len(self.items)
                            )
                        )
                temp_st = Structure()
                temp_st._skip_validation = getattr(instance, "_skip_validation", False)
                res = deque()
                for ind, item in enumerate(self.items):
                    if ind >= len(value):
                        continue
                    setattr(item, "_name", self._name + "_{}".format(str(ind)))
                    item.__set__(temp_st, value[ind])
                    res.append(getattr(temp_st, getattr(item, "_name")))
                for i in range(len(self.items), len(value)):
                    res.append(value[i])
                value = res

        super().__set__(instance, _DequeStruct(self, instance, value, self._name))


def verify_type_and_uniqueness(the_type, value, name, has_unique_items):
    if not isinstance(value, the_type):
        raise TypeError(
            "{}: Got {}; Expected {}".format(name, wrap_val(value), str(the_type))
        )
    if has_unique_items:
        unique = reduce(
            lambda unique_vals, x: unique_vals.append(x) or unique_vals
            if x not in unique_vals
            else unique_vals,
            value,
            [],
        )
        if len(unique) < len(value):
            raise ValueError(
                "{}: Got {}; Expected unique items".format(name, wrap_val(value))
            )


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

    def __set__(self, instance, value):
        verify_type_and_uniqueness(tuple, value, self._name, self.uniqueItems)
        if len(self.items) != len(value) and len(self.items) > 1:
            raise ValueError(
                "{}: Got {}; Expected a tuple of length {}".format(
                    self._name, wrap_val(value), len(self.items)
                )
            )

        temp_st = Structure()
        res = []
        items = self.items if len(self.items) > 1 else self.items * len(value)
        for ind, item in enumerate(items):
            setattr(item, "_name", self._name + "_{}".format(str(ind)))
            item.__set__(temp_st, value[ind])
            res.append(getattr(temp_st, getattr(item, "_name")))
            res += value[len(items) :]
        value = tuple(res)

        super().__set__(instance, value)


class Enum(Field, metaclass=_EnumMeta):
    """
    Enum field. value can be one of predefined values

    Arguments:
         values(`list` or `set` or `tuple`, alternatively an enum Type):
             allowed values. Can be of any type.
             Alternatively, can be an enum.Enum type. See example below.
             When defined with an enum.Enum, serialization converts to strings,
             while deserialization expects strings.
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
                        "{}: Got {}; Expected one of: {}".format(
                            self._name, value, ", ".join(enum_values)
                        )
                    )
                raise ValueError(
                    "{}: Got {}; Expected a value of {}".format(
                        self._name, value, self._enum_class
                    )
                )

        elif value not in self.values:
            raise ValueError(
                "{}: Got {}; Expected one of {}".format(
                    self._name, value, ", ".join([str(v) for v in self.values])
                )
            )

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


class Sized(Field):
    """
    The length of the value is limited to be at most the maximum given.
    The value can be any iterable.

        Arguments:

            maxlen(`int`):
                maximum length

    """

    def __init__(self, *args, maxlen, **kwargs):
        self.maxlen = maxlen
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if len(value) > self.maxlen:
            raise ValueError(
                "{}: Got {}; Expected a length up to {}".format(
                    self._name, value, self.maxlen
                )
            )
        super().__set__(instance, value)


class SizedString(String, Sized):
    pass


def _str_for_multioption_field(instance):
    name = instance.__class__.__name__
    if instance.get_fields():
        fields_st = ", ".join([str(field) for field in instance.get_fields()])
        propst = " [{}]".format(fields_st)
    else:
        propst = ""
    return "<{}{}>".format(name, propst)


class MultiFieldWrapper:
    """
    An abstract base class for AllOf, AnyOf, OneOf, etc.
    It provides flexibility in reading the "fields" argument.
    """

    def __init__(self, *arg, fields, **kwargs):
        if isinstance(fields, list):
            self._fields = []
            for item in fields:
                self._fields.append(_map_to_field(item))
        else:
            raise TypeError("Expected a Field class or instance")
        super().__init__(*arg, **kwargs)

    def get_fields(self):
        return self._fields


class AllOf(MultiFieldWrapper, Field, metaclass=_JSONSchemaDraft4ReuseMeta):
    """
    Content must adhere to all requirements in the fields arguments.
    Arguments:

        fields( `list` of :class:`Field`): optional
        the content should match all of the fields in the list

    Example:

    .. code-block:: python

        AllOf[Number(maximum=20, minimum=-10), Integer, Positive]

    """

    def __init__(self, fields):
        super().__init__(fields=fields)

    def __set__(self, instance, value):
        for field in self.get_fields():
            setattr(field, "_name", self._name)
            field.__set__(instance, value)
        super().__set__(instance, value)

    def __str__(self):
        return _str_for_multioption_field(self)


class AnyOf(MultiFieldWrapper, Field, metaclass=_JSONSchemaDraft4ReuseMeta):
    """
    Content must adhere to one or more of the requirements in the fields arguments.
    Arguments:

        fields( `list` of :class:`Field`): optional
        the content should match at least one of the fields in the list

    Example:

    .. code-block:: python

       AnyOf[Number(maximum=20, minimum=-10), Integer, Positive, String]

    """

    def __init__(self, fields):
        super().__init__(fields=fields)
        if fields:
            for f in fields:
                if isinstance(f, NoneField):
                    self._is_optional = True

    def __set__(self, instance, value):
        matched = False
        for field in self.get_fields():
            setattr(field, "_name", self._name)
            try:
                field.__set__(instance, value)
                matched = True
            except TypeError:
                pass
            except ValueError:
                pass
        if not matched:
            prefix = "{}: ".format(self._name) if self._name else ""
            raise ValueError(
                "{}{} Did not match any field option".format(prefix, wrap_val(value))
            )
        super().__set__(instance, value)

    def __str__(self):
        return _str_for_multioption_field(self)


class OneOf(MultiFieldWrapper, Field, metaclass=_JSONSchemaDraft4ReuseMeta):
    """
    Content must adhere to one, and only one, of the requirements in the fields arguments.
    Arguments:

        fields( `list` of :class:`Field`): optional
        the content should match one, and only one, of the fields in the list

    Example:

    .. code-block:: python

        OneOf[Number(maximum=20, minimum=-10), Integer, Positive, String]

    """

    def __init__(self, fields):
        super().__init__(fields=fields)

    def __set__(self, instance, value):
        matched = 0
        for field in self.get_fields():
            setattr(field, "_name", self._name)
            try:
                field.__set__(instance, value)
                matched += 1
            except TypeError:
                pass
            except ValueError:
                pass
        if not matched:
            raise ValueError(
                "{}: Got {}; Did not match any field option".format(self._name, value)
            )
        if matched > 1:
            raise ValueError(
                "{}: Got {}; Matched more than one field option".format(
                    self._name, value
                )
            )
        super().__set__(instance, value)

    def __str__(self):
        return _str_for_multioption_field(self)


class NotField(MultiFieldWrapper, Field, metaclass=_JSONSchemaDraft4ReuseMeta):
    """
    Content *must not* adhere to any of the requirements in the fields arguments.
    Arguments:

        fields( `list` of :class:`Field`): optional
            the content must not match any of the fields in the lists

    Examples:

    .. code-block:: python

        NotField([Number(multiplesOf=5, maximum=20, minimum=-10), String])
        NotField[Positive]

    """

    def __init__(self, fields):
        super().__init__(fields=fields)

    def __set__(self, instance, value):
        for field in self.get_fields():
            setattr(field, "_name", self._name)
            try:
                field.__set__(instance, value)
            except TypeError:
                pass
            except ValueError:
                pass
            else:
                raise ValueError(
                    "{}: Got {}; Expected not to match any field definition".format(
                        self._name, wrap_val(value)
                    )
                )
        super().__set__(instance, value)

    def __str__(self):
        return _str_for_multioption_field(self)


class ImmutableSet(Set, ImmutableField):
    """
    An immutable  :class:`Set`. Internally implemented by a Python frozenset, so it does not have
    any mutation methods. This makes it more developer-friendly.
    """

    _ty = frozenset

    def __set__(self, instance, value):
        if not isinstance(value, (set, frozenset)):
            raise TypeError(
                "{}: Got {}; Expected {}".format(self._name, wrap_val(value), set)
            )
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


class ImmutableMap(ImmutableField, Map):
    """
    An immutable version of :class:`Map`
    """

    pass


class ImmutableArray(ImmutableField, Array):
    """
    An immutable version of :class:`Array`
    """

    pass


class ImmutableDeque(ImmutableField, Deque):
    """
    An immutable version of :class:`Deque`
    """

    pass


class ImmutableString(ImmutableField, String):
    """
    An immutable version of :class:`String`
    """

    pass


class ImmutableNumber(ImmutableField, Number):
    """
    An immutable version of :class:`Number`
    """

    pass


class ImmutableInteger(ImmutableField, Integer):
    """
    An immutable version of :class:`Integer`
    """

    pass


class ImmutableFloat(ImmutableField, Float):  # pylint: disable=
    """
    An immutable version of :class:`Float`
    """

    pass


class ExceptionField(TypedField, SerializableField):
    """
    As Exception. This is serialized as the string representation of the exception.
    It does not support deserialization.
    """

    _ty = Exception

    def serialize(self, value):
        return "{}: {}".format(value.__class__.__name__, str(value))
