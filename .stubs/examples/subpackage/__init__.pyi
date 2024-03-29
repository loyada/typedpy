
#### This stub was autogenerated by Typedpy
###########################################

from typing import Union, Optional, Any, TypeVar, Type, NoReturn, Iterable
from typedpy import Structure

from datetime import datetime as datetime
from examples.more_classes import Person as Person
from examples.api_example import Foo as Foo
from typedpy import Omit as Omit
from typedpy import create_pyi as create_pyi
from examples.subpackage.apis import Vehicle as Vehicle


class FooOmitSubPackage(Structure):
    def __init__(
        self,
        i: int,
        s: str,
        person: Person,
        dob: datetime,
        arr: list[str],
        union: Union[int,str],
        any: Any,
        x: int,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...

    def shallow_clone_with_overrides(
        self,
        i: int = None,
        s: str = None,
        person: Person = None,
        dob: datetime = None,
        arr: list[str] = None,
        union: Union[int,str] = None,
        any: Any = None,
        x: int = None,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...

    @classmethod
    def from_other_class(
        cls,
        source_object: Any,
        *,
        ignore_props: Iterable[str] = None,
        i: int = None,
        s: str = None,
        person: Person = None,
        dob: datetime = None,
        arr: list[str] = None,
        union: Union[int,str] = None,
        any: Any = None,
        x: int = None,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...

    @classmethod
    def from_trusted_data(
        cls,
        source_object: Any = None,
        *,
        ignore_props: Iterable[str] = None,
        i: int = None,
        s: str = None,
        person: Person = None,
        dob: datetime = None,
        arr: list[str] = None,
        union: Union[int,str] = None,
        any: Any = None,
        x: int = None,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...


    i: int
    s: str
    person: Person
    dob: datetime
    arr: list[str]
    union: Union[int,str]
    any: Any
    x: int
    d: Optional[dict[str, int]] = None

