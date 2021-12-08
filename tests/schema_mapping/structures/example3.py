from typing import List, Optional

from typedpy import ImmutableStructure, Map, PositiveInt, Structure


class Person(ImmutableStructure):
    first_name: str
    last_name: str
    age: PositiveInt

    _optional = ["age"]


class Foo(Structure):
    i: Optional[int]
    s: Optional[str]


class Bar(Structure):
    people: List[Person]
    id: int


class Example3(Foo, Bar, ImmutableStructure):
    m: Map[str, Person]

