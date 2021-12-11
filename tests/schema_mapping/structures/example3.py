from typing import List, Optional

from typedpy import Array, ImmutableStructure, Map, PositiveInt, Structure


class Person(ImmutableStructure):
    first_name: str
    last_name: str
    age: PositiveInt

    _optional = ["age"]


class Groups(Structure):
    groups: Array[Person]


class Foo(Structure):
    i: Optional[int]
    s: Optional[str]


class Bar(Structure):
    people: List[Person]
    id: int


class Example3(Foo, Bar, ImmutableStructure):
    m: Map[str, Person]
    groups: Groups

