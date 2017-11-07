from collections import OrderedDict
from inspect import Signature, Parameter
import re


# support  json schema draft 4

def make_signature(names, required, additionalProperties):
    nonDefaultArgs = [Parameter(name, Parameter.POSITIONAL_OR_KEYWORD) for name in names if name in required]
    defaultArgs = [Parameter(name, Parameter.POSITIONAL_OR_KEYWORD, default=None) for name in names if
                   name not in required]
    addtionalArgs = [Parameter("kw", Parameter.VAR_KEYWORD)] if additionalProperties else []

    return Signature(nonDefaultArgs + defaultArgs + addtionalArgs)


class Field(object):
    def __init__(self, name=None):
        self.name = name

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value


class StructMeta(type):
    @classmethod
    def __prepare__(metacls, name, bases):
        return OrderedDict()

    def __new__(cls, name, bases, cls_dict):
        fields = [key for key, val in cls_dict.items() if isinstance(val, Field)]
        for field_name in fields:
            cls_dict[field_name].name = field_name
        clsobj = super().__new__(cls, name, bases, dict(cls_dict))
        clsobj._fields = fields
        required = cls_dict.get('_required', fields)
        additionalProps = cls_dict.get('_additionalProperties', True)
        sig = make_signature(clsobj._fields, required, additionalProps)
        setattr(clsobj, '__signature__', sig)
        return clsobj


class Structure(metaclass=StructMeta):
    _fields = []

    def __init__(self, *args, **kwargs):
        bound = self.__signature__.bind(*args, **kwargs)
        for name, val in bound.arguments.items():
            setattr(self, name, val)


class TypedField(Field):
    ty = object

    def __set__(self, instance, value):
        if not isinstance(value, self.ty):
            raise TypeError("%s: Expected %s" % (self.name, self.ty))
        super().__set__(instance, value)


class ClassReference(TypedField):
    def __init__(self, cls):
        self.ty = cls
        super().__init__(cls)


class Number(Field):
    def __init__(self, *args, multiplesOf=None, minimum=None, maximum=None, exclusiveMaximum=None, **kwargs):
        self.multiplesOf = multiplesOf
        self.minimum = minimum
        self.maximum = maximum
        self.exclusiveMaximum = exclusiveMaximum
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, float) and not isinstance(value, int):
            raise TypeError("{}: Expected a number".format(self.name))
        if isinstance(self.multiplesOf, float) and int(
                        value / self.multiplesOf) != value / self.multiplesOf or isinstance(self.multiplesOf,
                                                                                            int) and value % self.multiplesOf:
            raise ValueError("{}: Expected a a multiple of {}".format(self.name, self.multiplesOf))
        if (isinstance(self.minimum, float) or isinstance(self.minimum, int)) and self.minimum > value:
            raise ValueError("{}: Expected a minimum of {}".format(self.name, self.minimum))
        if (isinstance(self.maximum, float) or isinstance(self.maximum, int)):
            if self.exclusiveMaximum and self.maximum == value:
                raise ValueError("{}: Expected a maxmimum of less than {}".format(self.name, self.maximum))
            else:
                if self.maximum < value:
                    raise ValueError("{}: Expected a maxmimum of {}".format(self.name, self.maximum))
        super().__set__(instance, value)


class Integer(TypedField, Number):
    ty = int


class String(TypedField):
    ty = str

    def __init__(self, *args, minLength=None, maxLength=None, pattern=None, format=None, **kwargs):
        self.minLength = minLength
        self.maxLength = maxLength
        self.pattern = pattern
        if self.pattern is not None:
            self.compiledPattern = re.compile(self.pattern)
        self.format = format
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, str):
            raise TypeError("{}: Expected a string".format(self.name))
        if self.maxLength is not None and len(value)> self.maxLength:
            raise ValueError("{}: Expected a maxmimum length of {}".format(self.name, self.maxLength))
        if self.minLength is not None and len(value)< self.minLength:
            raise ValueError("{}: Expected a minimum length of {}".format(self.name, self.minLength))
        if self.pattern is not None and not self.compiledPattern.match(value):
            raise ValueError('{}: Does not match regular expression: {}'.format(self.name, self.pattern))

        super().__set__(instance, value)


class Float(TypedField, Number):
    ty = float



class Positive(Field):
    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError('{}: Must be positive'.format(self.name))
        super().__set__(instance, value)


class PositiveFloat(Float, Positive):
    pass


class PositiveInt(Integer, Positive):
    pass


class ListStruct(list):
    def __init__(self, array, struct_instance, mylist):
        self._array = array
        self._instance = struct_instance
        super().__init__(mylist)

    def __setitem__(self, key, value):
        copied = self.copy()
        copied.__setitem__(key, value)
        self._array.__set__(self._instance, copied)

class Array(TypedField):
    ty = list

    def __init__(self, *args, items=None, uniqueItems=None, minItems=None, maxItems=None, additionalItems = None, **kwargs):
        self.minItems = minItems
        self.maxItems = maxItems
        self.uniqueItems = uniqueItems
        self.additionalItems = additionalItems
        self.items = items
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if self.minItems is not None and len(value)<self.minItems:
            raise ValueError("{}: Expected length of at least {}".format(self.name, self.minItems))
        if self.maxItems is not None and len(value)>self.maxItems:
            raise ValueError("{}: Expected length of at most {}".format(self.name, self.maxItems))
        if self.uniqueItems and len(set(value))<len(value):
            raise ValueError("{}: Expected unique items".format(self.name))
        if self.items is not None:
            if isinstance(self.items, Field):
                tempSt = Structure()
                self.items.name = self.name
                res = []
                for i, v in enumerate(value):
                    self.items.name = self.name + "_{}".format(str(i))
                    self.items.__set__(tempSt, v)
                    res.append(getattr(tempSt, self.items.name))
                value = res
            elif isinstance(self.items, list):
                if len(self.items) > len(value) or (
                                    self.additionalItems is not None and self.additionalItems is False and len(self.items) > len(value)):
                    raise ValueError("{}: Expected an array of length {}".format(self.name, len(self.items)))
                tempSt = Structure()
                res = []
                for ind, item in enumerate(self.items):
                    item.name = self.name + "_{}".format(str(ind))
                    item.__set__(tempSt, value[ind])
                    res.append(getattr(tempSt, item.name))
                res += value[len(self.items):]
                value = res

        super().__set__(instance, ListStruct(self, instance, value))


class Enum(Field):
    def __init__(self, *args, values, **kwargs):
        self.values = values
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if value not in self.values:
            raise ValueError('{}: Must be one of {}'.format(self.name, self.values))
        super().__set__(instance, value)

class EnumString(Enum, String): pass

class Sized(Field):
    def __init__(self, *args, maxlen, **kwargs):
        self.maxlen = maxlen
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if len(value) > self.maxlen:
            raise ValueError('{}: Too long'.format(self.name))
        super().__set__(instance, value)


class SizedString(String, Sized):
    pass


class StructureReference(Field):
    counter = 0

    def __init__(self,  **kwargs):
        classname = "StructureReference_" + str(StructureReference.counter)
        StructureReference.counter+=1

        self.newclass = type(classname, (Structure,), kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, dict):
            raise TypeError("{}: Expected a dictionary".format(self.name))
        newval = self.newclass(**value)
        super().__set__(instance, newval)



class AllOf(Field):
    def __init__(self, fields):
        self.fields = fields

    def __set__(self, instance, value):
        for field in self.fields:
            field.name = self.name
            field.__set__(instance, value)
        super().__set__(instance, value)


class AnyOf(Field):
    def __init__(self, fields):
        self.fields = fields

    def __set__(self, instance, value):
        matched = False
        for field in self.fields:
            field.name = self.name
            try:
               field.__set__(instance, value)
               matched = True
            except: pass
        if not matched:
            raise ValueError("{}: Did not match any field option".format(self.name))
        super().__set__(instance, value)

class OneOf(Field):
    def __init__(self, fields):
        self.fields = fields

    def __set__(self, instance, value):
        matched = False
        for field in self.fields:
            field.name = self.name
            try:
               field.__set__(instance, value)
               if matched:
                   raise ValueError("{}: Matched more than one field option".format(self.name))
               matched = True
            except: pass
        if not matched:
            raise ValueError("{}: Did not match any field option".format(self.name))
        super().__set__(instance, value)


class NotField(Field):
    def __init__(self, field):
        self.field = field

    def __set__(self, instance, value):
        self.field.name = self.name
        try:
            self.field.__set__(instance, value)
        except:
            pass
        else:
            raise ValueError("expected not to match field definition")
        super().__set__(instance, value)


class Person(Structure):
    name = String(pattern='[A-Za-z]+$', maxLength=8)
    ssid = String(minLength = 3, pattern = '[A-Za-z]+$')
    num = Integer(maximum=30, minimum=10, multiplesOf="dd", exclusiveMaximum=False)
    foo = StructureReference(a=String(), b = StructureReference(c = Number(minimum=10), d = Number(maximum=10)))

class Trade(Structure):
    _additionalProperties = True
    _required = ['tradable', 'quantity', 'price']
    tradable = String()
    counterparty1 = String()
    counterparty2 = String()
    quantity = AnyOf([PositiveInt(), Enum(values=['asds', 'ddd', 'cxczx'])])
    price = PositiveFloat()
    category = EnumString(values = ['a','b'])
    person = ClassReference(Person)
    children = Array(uniqueItems=True, minItems= 3, items = [String(), Number(maximum=10)])



p = Person(name="fo", ssid="fff", num=25, foo = {'a': 'aaa', 'b': {'c': 10, 'd': 1}})
p.foo.b.c = 15
t = Trade(tradable="foo", quantity='ddd', price=10.0, category= 'a', children = ['aa', 3, 2])
t.children[1] = 8
print(t.__dict__)
