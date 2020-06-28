"""
Definitions of various types of fields. Supports JSON draft4 types.
"""
import re
from abc import ABC
from collections import OrderedDict
from functools import reduce
from decimal import Decimal, getcontext, InvalidOperation

from typedpy.structures import Field, Structure, TypedField, ClassReference, StructMeta, is_function_returning_field


def _map_to_field(item):
    if isinstance(item, StructMeta) and not isinstance(item, Field):
        return ClassReference(item)
    if item in [None, ''] or isinstance(item, Field):
        return item
    elif Field in getattr(item, '__mro__', []):
        return item()
    else:
        raise TypeError("Expected a Field/Structure class or Field instance")


def wrap_val(v): return "'{}'".format(v) if isinstance(v, str) else v


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

    """
    counter = 0

    def __init__(self, **kwargs):
        classname = "StructureReference_" + str(StructureReference.counter)
        StructureReference.counter += 1

        self._newclass = type(classname, (Structure,), kwargs)
        super().__init__(kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, dict):
            raise TypeError("{}: Expected a dictionary".format(self._name))
        newval = self._newclass(**value)
        super().__set__(instance, newval)

    def __str__(self):
        props = []
        for k, val in sorted(self._newclass.__dict__.items()):
            if val is not None and not k.startswith('_'):
                props.append('{} = {}'.format(k, str(val)))

        propst = '. Properties: {}'.format(', '.join(props)) if props else ''
        return '<Structure{}>'.format(propst)


class ImmutableField(Field):
    _immutable = True


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

    def __init__(self, *args, multiplesOf=None, minimum=None,
                 maximum=None, exclusiveMaximum=None, **kwargs):
        self.multiplesOf = multiplesOf
        self.minimum = minimum
        self.maximum = maximum
        self.exclusiveMaximum = exclusiveMaximum
        super().__init__(*args, **kwargs)

    @staticmethod
    def _validate_static(self, value):
        def is_number(val):
            return isinstance(val, (float, int, Decimal))

        def err_prefix():
            return "{}: Got {}; ".format(self._name, wrap_val(value)) if self._name else ""

        if not is_number(value):
            raise TypeError("{}Expected a number".format(err_prefix()))
        if isinstance(self.multiplesOf, float) and \
                int(value / self.multiplesOf) != value / self.multiplesOf or \
                isinstance(self.multiplesOf, int) and value % self.multiplesOf:
            raise ValueError("{}Expected a a multiple of {}".format(
                err_prefix(), self.multiplesOf))
        if (is_number(self.minimum)) and self.minimum > value:
            raise ValueError("{}Expected a minimum of {}".format(
                err_prefix(), self.minimum))
        if is_number(self.maximum):
            if self.exclusiveMaximum and self.maximum == value:
                raise ValueError("{}Expected a maximum of less than {}".format(
                    err_prefix(), self.maximum))
            else:
                if self.maximum < value:
                    raise ValueError("{}Expected a maximum of {}".format(
                        err_prefix(), self.maximum))

    def _validate(self, value):
        Number._validate_static(self, value)

    def __set__(self, instance, value):
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


class DecimalNumber(Number):
    """
    An extension of :class:`Number` for a Decimal. Accepts anything that can be converted to a Decimal
    """

    def __set__(self, instance, value):
        try:
            value = Decimal(value)
        except TypeError as ex:
            raise TypeError("{}: {}".format(self._name, ex.args[0]))
        except InvalidOperation as ex:
            raise ValueError("{}: {}".format(self._name, ex.args[0]))

        super().__set__(instance, value)


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

    def __init__(self, *args, minLength=None, maxLength=None,
                 pattern=None, **kwargs):
        self.minLength = minLength
        self.maxLength = maxLength
        self.pattern = pattern
        if self.pattern is not None:
            self._compiled_pattern = re.compile(self.pattern)
        super().__init__(*args, **kwargs)

    def _validate(self, value):
        String._validate_static(self, value)

    @staticmethod
    def _validate_static(self, value):
        def err_prefix():
            return "{}: Got {}; ".format(self._name, wrap_val(value)) if self._name else ""

        if not isinstance(value, str):
            raise TypeError("{}Expected a string".format(err_prefix()))
        if self.maxLength is not None and len(value) > self.maxLength:
            raise ValueError("{}Expected a maximum length of {}".format(
                err_prefix(), self.maxLength))
        if self.minLength is not None and len(value) < self.minLength:
            raise ValueError("{}Expected a minimum length of {}".format(
                err_prefix(), self.minLength))
        if self.pattern is not None and not self._compiled_pattern.match(value):
            raise ValueError('{}Does not match regular expression: "{}"'.format(
                err_prefix(), self.pattern))

    def __set__(self, instance, value):
        self._validate(value)
        super().__set__(instance, value)


def _foo(): pass


class Function(Field):
    """
       A function. Note that this can't be any callable (it can't be a class, for example), but a real function
    """
    def __set__(self, instance, value):
        def is_function(f):
            return type(f) == type(_foo) or type(f) == type(open)

        def err_prefix():
            return "{}: Got {}; ".format(self._name, wrap_val(value)) if self._name else ""

        if not is_function(value):
            raise TypeError("{}Expected a function".format(err_prefix()))
        super().__set__(instance, value)


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
            raise ValueError('{}: Must be positive'.format(self._name))
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


class _ListStruct(list):
    """
    This is a useful wrapper for the content of list in an Array field.
    It ensures that an update of the form:
     mystruct.my_array[i] = new_val
    Will not bypass the validation of the Array.
    """

    def __init__(self, array, struct_instance, mylist):
        self._array = array
        self._instance = struct_instance
        super().__init__(mylist)

    def __setitem__(self, key, value):
        copied = self.copy()
        copied.__setitem__(key, value)
        setattr(self._instance, getattr(self._array, '_name', None), copied)

    def append(self, value):
        copied = self.copy()
        copied.append(value)
        setattr(self._instance, getattr(self._array, '_name', None), copied)

    def extend(self, value):
        copied = self.copy()
        copied.extend(value)
        setattr(self._instance, getattr(self._array, '_name', None), copied)
        setattr(self._instance, getattr(self._array, '_name', None), copied)

    def insert(self, index: int, value):
        copied = self.copy()
        copied.insert(index, value)
        setattr(self._instance, getattr(self._array, '_name', None), copied)

    def remove(self, ind):
        copied = self.copy()
        copied.remove(ind)
        setattr(self._instance, getattr(self._array, '_name', None), copied)

    def pop(self, index: int = -1):
        copied = self.copy()
        res = copied.pop(index)
        setattr(self._instance, getattr(self._array, '_name', None), copied)
        return res


class _DictStruct(dict):
    """
    This is a useful wrapper for the content of dict in an Map field.
    It ensures that an update of the form:
     mystruct.my_map[i] = new_val, or
     mystruct.my_map.update(some_dict)

    ...will not bypass the validation of the Map.
    """

    def __init__(self, the_map, struct_instance, mydict):
        self._map = the_map
        self._instance = struct_instance
        super().__init__(mydict)

    def __setitem__(self, key, value):
        copied = self.copy()
        copied.__setitem__(key, value)
        setattr(self._instance, getattr(self._map, '_name', None), copied)

    def __delitem__(self, key):
        copied = self.copy()
        del copied[key]
        setattr(self._instance, getattr(self._map, '_name', None), copied)

    def update(self, *args, **kwargs):
        copied = self.copy()
        res = copied.update(*args, **kwargs)
        setattr(self._instance, getattr(self._map, '_name', None), copied)
        return res


class _CollectionMeta(type):
    def __getitem__(cls, item):
        def validate_and_get_field(val):
            if isinstance(val, Field):
                return val
            elif Field in getattr(val, '__mro__', {}):
                return val()
            elif Structure in getattr(val, '__mro__', {}):
                return ClassReference(val)
            elif is_function_returning_field(val):
                return val()
            else:
                raise TypeError("Expected a Field class or instance")

        if isinstance(item, tuple):
            items = [validate_and_get_field(it) for it in item]
            return cls(items=items)
        return cls(items=validate_and_get_field(item))


class _EnumMeta(type):
    def __getitem__(cls, values):
        return cls(values=list(values))


class _JSONSchemaDraft4ReuseMeta(type):
    def __getitem__(cls, item):
        def validate_and_get_field(val):
            if isinstance(val, Field):
                return val
            elif Field in getattr(val, '__mro__', {}):
                return val()
            elif Structure in getattr(val, '__mro__', {}):
                return ClassReference(val)
            elif is_function_returning_field(val):
                return val()
            else:
                raise TypeError("Expected a Field class or instance")

        if isinstance(item, tuple):
            fields = [validate_and_get_field(it) for it in item]
            return cls(fields)
        return cls([validate_and_get_field(item)])


class SizedCollection(object):
    def __init__(self, *args, minItems=None, maxItems=None, **kwargs):
        self.minItems = minItems
        self.maxItems = maxItems
        super().__init__(*args, **kwargs)

    def validate_size(self, items, name):
        if self.minItems is not None and len(items) < self.minItems:
            raise ValueError("{}: Expected length of at least {}".format(
                name, self.minItems))
        if self.maxItems is not None and len(items) > self.maxItems:
            raise ValueError("{}: Expected length of at most {}".format(
                name, self.maxItems))


class Set(SizedCollection, TypedField, metaclass=_CollectionMeta):
    """
    A set collection. Accepts input of type `set`

    Arguments:
        minItems(int): optional
            minimal size
        maxItems(int): optional
            maximal size
        items(:class:`Field` or :class:`Structure`): optional
            The type of the content, can be a predefined :class:`Structure` or
            :class:`Field`

    Examples:

    .. code-block:: python

        Set[String]
        Set(items=Integer(maximum=10), maxItems = 10)

        # let's assume we defined a Structure 'Person', then we can use it too:
        Set[Person]


    """
    _ty = set

    def __init__(self, *args, items=None,
                 **kwargs):
        self.items = _map_to_field(items)

        if isinstance(self.items, TypedField) and not \
                getattr(getattr(self.items, '_ty'), '__hash__'):
            raise TypeError("Set element of type {} is not hashable".format(
                getattr(self.items, '_ty')))
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, set):
            raise TypeError("{}: Got {}; Expected {}".format(self._name, wrap_val(value), set))
        self.validate_size(value, self._name)
        if self.items is not None:
            temp_st = Structure()
            setattr(self.items, '_name', self._name)
            res = set()
            for val in value:
                self.items.__set__(temp_st, val)
                res.add(getattr(temp_st, getattr(self.items, '_name')))
                value = res
        super().__set__(instance, value)


class Map(SizedCollection, TypedField, metaclass=_CollectionMeta):
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

    def __init__(self, *args, items=None,
                 **kwargs):
        if items is not None and (not isinstance(items, (tuple, list)) or len(items) != 2):
            raise TypeError("items is expected to be a list/tuple of two fields")
        if items is None:
            self.items = None
        else:
            self.items = []
            for item in items:
                self.items.append(_map_to_field(item))
            key_field = self.items[0]
            if isinstance(key_field, TypedField) and not getattr(getattr(key_field, '_ty'), '__hash__'):
                raise TypeError("Key field of type {}, with underlying type of {} is not hashable".format(
                    key_field, getattr(key_field, '_ty')))
        self._custom_deep_copy_implementation = True
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, dict):
            raise TypeError("%s: Expected %s" % (self._name, dict))
        self.validate_size(value, self._name)

        if self.items is not None:
            temp_st = Structure()
            key_field, value_field = self.items[0], self.items[1]
            setattr(key_field, '_name', self._name + '_key')
            setattr(value_field, '_name', self._name + '_value')
            res = OrderedDict()

            for key, val in value.items():
                key_field.__set__(temp_st, key)
                value_field.__set__(temp_st, val)
                res[getattr(temp_st, getattr(key_field, '_name'))] = getattr(
                    temp_st, getattr(value_field, '_name'))
            value = res
        super().__set__(instance, _DictStruct(self, instance, value))


class Array(SizedCollection, TypedField, metaclass=_CollectionMeta):
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

    """
    _ty = list

    def __init__(self, *args, items=None, uniqueItems=None, additionalItems=None,
                 **kwargs):
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

    def __set__(self, instance, value):
        verify_type_and_uniqueness(list, value, self._name, self.uniqueItems)
        self.validate_size(value, self._name)
        if self.items is not None:
            if isinstance(self.items, Field):
                temp_st = Structure()
                setattr(self.items, '_name', self._name)
                res = []
                for i, val in enumerate(value):
                    setattr(self.items, '_name', self._name + "_{}".format(str(i)))
                    self.items.__set__(temp_st, val)
                    res.append(getattr(temp_st, getattr(self.items, '_name')))
                value = res
            elif isinstance(self.items, list):
                additional_properties_forbidden = self.additionalItems is not None and \
                                                  self.additionalItems is False
                if len(self.items) > len(value) or \
                        (additional_properties_forbidden and len(self.items) > len(value)):
                    raise ValueError("{}: Got {}; Expected an array of length {}".format(
                        self._name, value, len(self.items)))
                temp_st = Structure()
                res = []
                for ind, item in enumerate(self.items):
                    setattr(item, '_name', self._name + "_{}".format(str(ind)))
                    item.__set__(temp_st, value[ind])
                    res.append(getattr(temp_st, getattr(item, '_name')))
                res += value[len(self.items):]
                value = res

        super().__set__(instance, _ListStruct(self, instance, value))


def verify_type_and_uniqueness(the_type, value, name, has_unique_items):
    if not isinstance(value, the_type):
        raise TypeError("{}: Got {}; Expected {}".format(name, wrap_val(value), str(the_type)))
    if has_unique_items:
        unique = reduce(lambda unique_vals, x: unique_vals.append(x) or
                        unique_vals if x not in unique_vals
                        else unique_vals, value, [])
        if len(unique) < len(value):
            raise ValueError("{}: Got {}; Expected unique items".format(name, wrap_val(value)))


class Tuple(TypedField, metaclass=_CollectionMeta):
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

        // a is a tuple of exactly 2 strings that are different from each other.
        a = Tuple(uniqueItems=True, items = [String, String])

        // b is a tuple of 3: string, string and a number up to 10.
        b = Tuple(items = [String, String, Number(maximum=10)])

        // c is a tuple of 3: integer, string, float.
        c = Tuple[Integer, String, Float]

        // The following define a tuple of any number of Integers
        d = Tuple[Integer]

        // It can also contain other structures:
        // Assume we have something like: class Foo(Structure): pass
        // e is a tuple of any number of Integers or Foo instances
        e = Tuple[AnyOf[Integer, Foo]]

    """
    _ty = tuple

    def __init__(self, *args, items, uniqueItems=None,
                 **kwargs):
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

    def __set__(self, instance, value):
        verify_type_and_uniqueness(tuple, value, self._name, self.uniqueItems)
        if len(self.items) != len(value) and len(self.items) > 1:
            raise ValueError("{}: Got {}; Expected a tuple of length {}".format(
                self._name, wrap_val(value), len(self.items)))

        temp_st = Structure()
        res = []
        items = self.items if len(self.items) > 1 else self.items * len(value)
        for ind, item in enumerate(items):
            setattr(item, '_name', self._name + "_{}".format(str(ind)))
            item.__set__(temp_st, value[ind])
            res.append(getattr(temp_st, getattr(item, '_name')))
            res += value[len(items):]
        value = tuple(res)

        super().__set__(instance, value)


class Enum(Field, metaclass=_EnumMeta):
    """
        Enum field. value can be one of predefined values

        Arguments:
             values(`list` or `set` or `tuple`):
                 allowed values. Can be of any type

    """

    def __init__(self, *args, values, **kwargs):
        self.values = values
        super().__init__(*args, **kwargs)

    def _validate(self, value):
        if value not in self.values:
            raise ValueError('{}: Must be one of {}'.format(self._name, self.values))

    def __set__(self, instance, value):
        self._validate(value)
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
            raise ValueError('{}: Too long'.format(self._name))
        super().__set__(instance, value)


class SizedString(String, Sized):
    pass


def _str_for_multioption_field(instance):
    name = instance.__class__.__name__
    if instance.get_fields():
        fields_st = ', '.join([str(field) for field in instance.get_fields()])
        propst = ' [{}]'.format(fields_st)
    else:
        propst = ''
    return '<{}{}>'.format(name, propst)


class MultiFieldWrapper(object):
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
            setattr(field, '_name', self._name)
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

    def __set__(self, instance, value):
        matched = False
        for field in self.get_fields():
            setattr(field, '_name', self._name)
            try:
                field.__set__(instance, value)
                matched = True
            except TypeError:
                pass
            except ValueError:
                pass
        if not matched:
            raise ValueError("{}: {} Did not match any field option".format(self._name, wrap_val(value)))
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
            setattr(field, '_name', self._name)
            try:
                field.__set__(instance, value)
                matched += 1
            except TypeError:
                pass
            except ValueError:
                pass
        if not matched:
            raise ValueError("{}: Got {}; Did not match any field option".format(self._name, value))
        if matched > 1:
            raise ValueError("{}: Got {}; Matched more than one field option".format(self._name, value))
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
            setattr(field, '_name', self._name)
            try:
                field.__set__(instance, value)
            except TypeError:
                pass
            except ValueError:
                pass
            else:
                raise ValueError("{}: Got {}; Expected not to match any field definition".
                                 format(self._name, wrap_val(value)))
        super().__set__(instance, value)

    def __str__(self):
        return _str_for_multioption_field(self)


class ValidatedTypedField(TypedField):

    def __set__(self, instance, value):
        self._validate_func(value)  # pylint: disable=E1101
        super().__set__(instance, value)


def create_typed_field(classname, cls, validate_func=None):
    """
    Factory that generates a new class for a :class:`Field` as a wrapper of any class.
    Example:
    Given a class Foo, and a validation function for the value in Foo - validate_foo, the line

    .. code-block:: python

        ValidatedFooField = create_typed_field("FooField", Foo, validate_func=validate_foo)

    Generates a new :class:`Field` class that validates the content using validate_foo, and can be
    used just like any :class:`Field` type.

    .. code-block:: python

        class A(Structure):
            foo = ValidatedFooField
            bar = Integer

        # asumming we have an instance of Foo, called my_foo:
        A(bar=4, foo=my_foo)

    Arguments:

        classname(`str`):
            the content must not match any of the fields in the lists
    """

    def validate_wrapper(cls, value):
        if validate_func is None:
            return
        validate_func(value)

    return type(classname, (ValidatedTypedField,), {'_validate_func': validate_wrapper, '_ty': cls})


class SerializableField(ABC):
    """
    An abstract class for a field that has custom serialization or deserialization.
    can override the method:
      serialize(self, value),
      deserialize(self, value)
    """

    def serialize(self, value): return value

    def deserialize(self, value): return value

