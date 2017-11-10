from  structures import  Field, Structure
import re


class TypedField(Field):
    _ty = object

    def __set__(self, instance, value):
        if not isinstance(value, self._ty):
            raise TypeError("%s: Expected %s" % (self._name, self._ty))
        super().__set__(instance, value)


class ClassReference(TypedField):
    def __init__(self, cls):
        self._ty = cls
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
            raise TypeError("{}: Expected a number".format(self._name))
        if isinstance(self.multiplesOf, float) and int(
                        value / self.multiplesOf) != value / self.multiplesOf or isinstance(self.multiplesOf,
                                                                                            int) and value % self.multiplesOf:
            raise ValueError("{}: Expected a a multiple of {}".format(self._name, self.multiplesOf))
        if (isinstance(self.minimum, float) or isinstance(self.minimum, int)) and self.minimum > value:
            raise ValueError("{}: Expected a minimum of {}".format(self._name, self.minimum))
        if (isinstance(self.maximum, float) or isinstance(self.maximum, int)):
            if self.exclusiveMaximum and self.maximum == value:
                raise ValueError("{}: Expected a maxmimum of less than {}".format(self._name, self.maximum))
            else:
                if self.maximum < value:
                    raise ValueError("{}: Expected a maxmimum of {}".format(self._name, self.maximum))
        super().__set__(instance, value)


class Integer(TypedField, Number):
    _ty = int


class String(TypedField):
    _ty = str

    def __init__(self, *args, minLength=None, maxLength=None, pattern=None, format=None, **kwargs):
        self.minLength = minLength
        self.maxLength = maxLength
        self.pattern = pattern
        if self.pattern is not None:
            self._compiledPattern = re.compile(self.pattern)
        self.format = format
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, str):
            raise TypeError("{}: Expected a string".format(self._name))
        if self.maxLength is not None and len(value)> self.maxLength:
            raise ValueError("{}: Expected a maxmimum length of {}".format(self._name, self.maxLength))
        if self.minLength is not None and len(value)< self.minLength:
            raise ValueError("{}: Expected a minimum length of {}".format(self._name, self.minLength))
        if self.pattern is not None and not self._compiledPattern.match(value):
            raise ValueError('{}: Does not match regular expression: {}'.format(self._name, self.pattern))

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
    _ty = list

    def __init__(self, *args, items=None, uniqueItems=None, minItems=None, maxItems=None, additionalItems = None, **kwargs):
        self.minItems = minItems
        self.maxItems = maxItems
        self.uniqueItems = uniqueItems
        self.additionalItems = additionalItems
        self.items = items
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if self.minItems is not None and len(value)<self.minItems:
            raise ValueError("{}: Expected length of at least {}".format(self._name, self.minItems))
        if self.maxItems is not None and len(value)>self.maxItems:
            raise ValueError("{}: Expected length of at most {}".format(self._name, self.maxItems))
        if self.uniqueItems and len(set(value))<len(value):
            raise ValueError("{}: Expected unique items".format(self.name))
        if self.items is not None:
            if isinstance(self.items, Field):
                tempSt = Structure()
                self.items._name = self._name
                res = []
                for i, v in enumerate(value):
                    self.items._name = self._name + "_{}".format(str(i))
                    self.items.__set__(tempSt, v)
                    res.append(getattr(tempSt, self.items.name))
                value = res
            elif isinstance(self.items, list):
                if len(self.items) > len(value) or (
                                    self.additionalItems is not None and self.additionalItems is False and len(self.items) > len(value)):
                    raise ValueError("{}: Expected an array of length {}".format(self._name, len(self.items)))
                tempSt = Structure()
                res = []
                for ind, item in enumerate(self.items):
                    item._name = self._name + "_{}".format(str(ind))
                    item.__set__(tempSt, value[ind])
                    res.append(getattr(tempSt, item._name))
                res += value[len(self.items):]
                value = res

        super().__set__(instance, ListStruct(self, instance, value))


class Enum(Field):
    def __init__(self, *args, values, **kwargs):
        self.values = values
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if value not in self.values:
            raise ValueError('{}: Must be one of {}'.format(self._name, self.values))
        super().__set__(instance, value)

class EnumString(Enum, String): pass

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


class StructureReference(Field):
    counter = 0

    def __init__(self,  **kwargs):
        classname = "StructureReference_" + str(StructureReference.counter)
        StructureReference.counter+=1

        self._newclass = type(classname, (Structure,), kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, dict):
            raise TypeError("{}: Expected a dictionary".format(self._name))
        newval = self._newclass(**value)
        super().__set__(instance, newval)

    def __str__(self):
        props = []
        for k, v in self._newclass.__dict__.items():
            if v is not None and  not k.startswith('_'):
                props.append('{} = {}'.format(k, str(v)))

        propst = '. Properties: {}'.format(', '.join(props)) if  props  else ''
        return '<Structure{}>'.format(propst)



class AllOf(Field):
    def __init__(self, fields):
        self.fields = fields

    def __set__(self, instance, value):
        for field in self.fields:
            field._name = self._name
            field.__set__(instance, value)
        super().__set__(instance, value)


class AnyOf(Field):
    def __init__(self, fields):
        self.fields = fields

    def __set__(self, instance, value):
        matched = False
        for field in self.fields:
            field._name = self._name
            try:
               field.__set__(instance, value)
               matched = True
            except: pass
        if not matched:
            raise ValueError("{}: Did not match any field option".format(self._name))
        super().__set__(instance, value)

class OneOf(Field):
    def __init__(self, fields):
        self.fields = fields

    def __set__(self, instance, value):
        matched = False
        for field in self.fields:
            field._name = self._name
            try:
               field.__set__(instance, value)
               if matched:
                   raise ValueError("{}: Matched more than one field option".format(self._name))
               matched = True
            except: pass
        if not matched:
            raise ValueError("{}: Did not match any field option".format(self._name))
        super().__set__(instance, value)


class NotField(Field):
    def __init__(self, field):
        self.field = field

    def __set__(self, instance, value):
        self.field._name = self._name
        try:
            self.field.__set__(instance, value)
        except:
            pass
        else:
            raise ValueError("expected not to match field definition")
        super().__set__(instance, value)

