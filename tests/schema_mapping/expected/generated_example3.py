from typedpy import *


class Person(Structure):
    first_name = String()
    last_name = String()
    age = Integer(minimum=1)

    _required = ['first_name', 'last_name']

# ********************


class Example1(Structure):
    people = Array(items=Person)
    id = Integer()
    i = Integer()
    s = String()
    m = Map(items=[String(), Person])

    _required = ['id', 'm', 'people']
