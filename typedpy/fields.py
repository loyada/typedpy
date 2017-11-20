"""
Definitions of various types of fields. Supports JSON draft4 types.
"""
import re
from functools import reduce

from typedpy.structures import Field, Structure, TypedField


class Number(Field):
    """
    Base class for numerical fields. Based on Json schema draft4.
    """

    def __init__(self, *args, multiplesOf=None, minimum=None,
                 maximum=None, exclusiveMaximum=None, **kwargs):
        self.multiplesOf = multiplesOf
        self.minimum = minimum
        self.maximum = maximum
        self.exclusiveMaximum = exclusiveMaximum
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        def is_number(val):
            return isinstance(val, (float, int))

        if not isinstance(value, float) and not isinstance(value, int):
            raise TypeError("{}: Expected a number".format(self._name))
        if isinstance(self.multiplesOf, float) and \
                        int(value / self.multiplesOf) != value / self.multiplesOf or \
                        isinstance(self.multiplesOf, int) and value % self.multiplesOf:
            raise ValueError("{}: Expected a a multiple of {}".format(
                self._name, self.multiplesOf))
        if (is_number(self.minimum)) and self.minimum > value:
            raise ValueError("{}: Expected a minimum of {}".format(
                self._name, self.minimum))
        if is_number(self.maximum):
            if self.exclusiveMaximum and self.maximum == value:
                raise ValueError("{}: Expected a maxmimum of less than {}".format(
                    self._name, self.maximum))
            else:
                if self.maximum < value:
                    raise ValueError("{}: Expected a maxmimum of {}".format(
                        self._name, self.maximum))
        super().__set__(instance, value)


class Integer(TypedField, Number):
    _ty = int


class String(TypedField):
    _ty = str

    def __init__(self, *args, minLength=None, maxLength=None,
                 pattern=None, format_type=None, **kwargs):
        self.minLength = minLength
        self.maxLength = maxLength
        self.pattern = pattern
        if self.pattern is not None:
            self._compiled_pattern = re.compile(self.pattern)
        self.format_type = format_type
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, str):
            raise TypeError("{}: Expected a string".format(self._name))
        if self.maxLength is not None and len(value) > self.maxLength:
            raise ValueError("{}: Expected a maxmimum length of {}".format(
                self._name, self.maxLength))
        if self.minLength is not None and len(value) < self.minLength:
            raise ValueError("{}: Expected a minimum length of {}".format(
                self._name, self.minLength))
        if self.pattern is not None and not self._compiled_pattern.match(value):
            raise ValueError('{}: Does not match regular expression: {}'.format(
                self._name, self.pattern))

        super().__set__(instance, value)


class Float(TypedField, Number):
    _ty = float


class Boolean(TypedField):
    _ty = bool


class Positive(Field):
    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError('{}: Must be positive'.format(self._name))
        super().__set__(instance, value)


class PositiveFloat(Float, Positive):
    pass


class PositiveInt(Integer, Positive):
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
        self._array.__set__(self._instance, copied)


class _DickStruct(dict):
    """
    This is a useful wrapper for the content of dict in an Map field.
    It ensures that an update of the form:
     mystruct.my_map[i] = new_val
    Will not bypass the validation of the Map.
    """

    def __init__(self, the_map, struct_instance, mydict):
        self._map = the_map
        self._instance = struct_instance
        super().__init__(mydict)

    def __setitem__(self, key, value):
        copied = self.copy()
        copied.__setitem__(key, value)
        self._map.__set__(self._instance, copied)

    def __delitem__(self, key):
        copied = self.copy()
        del copied[key]
        self._map.__set__(self._instance, copied)

    def update(self, *args, **kwargs):
        copied = self.copy()
        res = copied.update(*args, **kwargs)
        self._map.__set__(self._instance, copied)
        return res


class _CollectionMeta(type):
    def __getitem__(cls, item):
        def validate_and_get_field(val):
            if isinstance(val, Field):
                return val
            elif Field in val.__mro__:
                return val()
            else:
                raise TypeError("Expected a Field class or instance")

        if isinstance(item, tuple):
            items = [validate_and_get_field(it) for it in item]
            return cls(items=items)
        return cls(items=validate_and_get_field(item))


class _JSONSchemaDraft4ReuseMeta(type):
    def __getitem__(cls, item):
        def validate_and_get_field(val):
            if isinstance(val, Field):
                return val
            elif Field in val.__mro__:
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
    _ty = set

    def __init__(self, *args, items=None,
                 **kwargs):
        if items is None or isinstance(items, Field):
            self.items = items
        elif Field in getattr(items, '__mro__', []):
            self.items = items()
        else:
            raise TypeError("Expected a Field class or instance")
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, set):
            raise TypeError("%s: Expected %s" % (self._name, set))
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
                if isinstance(item, Field):
                    self.items.append(item)
                elif Field in item.__mro__:
                    self.items.append(item())
                else:
                    raise TypeError("Expected a Field class or instance")
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
            res = {}

            for key, val in value.items():
                key_field.__set__(temp_st, key)
                value_field.__set__(temp_st, val)
                res[getattr(temp_st, getattr(key_field, '_name'))] = getattr(
                    temp_st, getattr(value_field, '_name'))
            value = res

        super().__set__(instance, _DickStruct(self, instance, value))


class Array(SizedCollection, TypedField, metaclass=_CollectionMeta):
    _ty = list

    def __init__(self, *args, items=None, uniqueItems=None, additionalItems=None,
                 **kwargs):
        self.uniqueItems = uniqueItems
        self.additionalItems = additionalItems
        if isinstance(items, list):
            self.items = []
            for item in items:
                if isinstance(item, Field):
                    self.items.append(item)
                elif Field in item.__mro__:
                    self.items.append(item())
                else:
                    raise TypeError("Expected a Field class or instance")
        else:
            self.items = items
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, list):
            raise TypeError("%s: Expected %s" % (self._name, list))
        self.validate_size(value, self._name)
        if self.uniqueItems:
            unique = reduce(lambda unique_vals, x: unique_vals.append(x) or
                            unique_vals if x not in unique_vals
                            else unique_vals, value, [])
            if len(unique) < len(value):
                raise ValueError("{}: Expected unique items".format(self._name))
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
                    raise ValueError("{}: Expected an array of length {}".format(
                        self._name, len(self.items)))
                temp_st = Structure()
                res = []
                for ind, item in enumerate(self.items):
                    setattr(item, '_name', self._name + "_{}".format(str(ind)))
                    item.__set__(temp_st, value[ind])
                    res.append(getattr(temp_st, getattr(item, '_name')))
                res += value[len(self.items):]
                value = res

        super().__set__(instance, _ListStruct(self, instance, value))


class Enum(Field):
    def __init__(self, *args, values, **kwargs):
        self.values = values
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if value not in self.values:
            raise ValueError('{}: Must be one of {}'.format(self._name, self.values))
        super().__set__(instance, value)


class EnumString(Enum, String):
    pass


class Sized(Field):
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
    def __init__(self, *arg, fields, **kwargs):
        if isinstance(fields, list):
            self._fields = []
            for item in fields:
                if isinstance(item, Field):
                    self._fields.append(item)
                elif Field in item.__mro__:
                    self._fields.append(item())
                else:
                    raise TypeError("Expected a Field class or instance")
        else:
            raise TypeError("Expected a Field class or instance")
        super().__init__(*arg, **kwargs)

    def get_fields(self):
        return self._fields


class AllOf(MultiFieldWrapper, Field, metaclass=_JSONSchemaDraft4ReuseMeta):
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
            raise ValueError("{}: Did not match any field option".format(self._name))
        super().__set__(instance, value)

    def __str__(self):
        return _str_for_multioption_field(self)


class OneOf(MultiFieldWrapper, Field, metaclass=_JSONSchemaDraft4ReuseMeta):
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
            raise ValueError("{}: Did not match any field option".format(self._name))
        if matched > 1:
            raise ValueError("{}: Matched more than one field option".format(self._name))
        super().__set__(instance, value)

    def __str__(self):
        return _str_for_multioption_field(self)


class NotField(MultiFieldWrapper, Field, metaclass=_JSONSchemaDraft4ReuseMeta):
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
                raise ValueError("{}: Expected not to match any field definition".
                                 format(self._name))
        super().__set__(instance, value)

    def __str__(self):
        return _str_for_multioption_field(self)
