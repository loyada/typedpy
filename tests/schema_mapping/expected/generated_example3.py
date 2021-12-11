from typedpy import *


class Person(Structure):
    first_name = String()
    last_name = String()
    age = Integer(minimum=1)

    _required = ['first_name', 'last_name']


class Groups(Structure):
    groups = Array(items=Person)

    _required = ['groups']

# ********************


class Example1(Structure):
    people = Array(items=Person)
    id = Integer()
    i = Integer()
    s = String()
    m = Map(items=[String(), Person])
    groups = Groups

    _required = ['groups', 'id', 'm', 'people']
