from contextlib import AbstractContextManager

from typedpy import Field, Structure, Integer, String


class LinkedField:
    def __init__(self, instance: Structure, field_name):
        if field_name not in instance.get_all_fields_by_name():
            raise ValueError("field {} does not exist in {}".format(field_name, instance))
        self._field_name = field_name
        self._instance = instance
        self._loct = True
        self._instantiated = True

    def __getattr__(self, item):
        if item == '_instantiated':
            return super(LinkedField, self).__getattr__(item)
        value = getattr(self._instance, self._field_name, None)
        if value is None:
            raise ValueError("value is None")
        return getattr(value, item, None)

    def __setattr__(self, key, value):
        if not getattr(self, '_instantiated', None):
            super().__setattr__(key, value)
        else:
            value = getattr(self._instance, self._field_name, None)
            if value is None:
                raise ValueError("value is None")
            setattr(value, key, value)

    def __eq__(self, other):
        value = getattr(self._instance, self._field_name, None)
        return value==other

    def __add__(self, other):
        value = getattr(self._instance, self._field_name, None)
        return value + other

    def __sub__(self, other):
        value = getattr(self._instance, self._field_name, None)
        return value - other

    def __mul__(self, other):
        value = getattr(self._instance, self._field_name, None)
        return value * other


class Foo(Structure):
    x: list[str]

foo = Foo(x=['abc'])
x = foo.x
x.append('xyz')
x += [123]
print(x==['abc', 'xyz'])
print(foo.x)

foo = Foo(x=['abc'])
x=LinkedField(foo, 'x')
x.append('xyz')
x += [123]
print(x==['abc', 'xyz'])
print(foo.x)
