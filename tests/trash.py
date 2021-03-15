from typing import Optional

from typedpy import ImmutableStructure, PositiveInt, String, Array, Field, Map, Integer


def Name() -> Field: return String(minLength=4, maxLength=40)



class Man(ImmutableStructure):
        email = Map[String, String]
        name = String
        a = Integer
        _required = []


man = Man(a=None)

print(man)

import HTTPStatus