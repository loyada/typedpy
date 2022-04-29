
# i: int
# d: dict
# s: str
# union: Union[int, str]
# any: Any
# x: int

# asdasd is invalid.
# append is invalid
# bar = Bar(i=5, d={}, s="xyz", union="union", any=[1,2,"xxx"], x="xxxx", opt="opt", asdasd=234234)
# bar.i.append(4)
from datetime import datetime
from typing import Optional

from examples.api_example import Bar, Foo
from examples.enums import State
from examples.more_classes import Person




bar = Bar(
    i=5,
    d={},
    s="xyz",
    union=4,
    any=[1, 2, "xxx"],
    x=234,
    opt=11,
    state=State.NY,
    dob=datetime.now(),
    person=Person(),
    arr = []
)

bar.shallow_clone_with_overrides(i="xyz", state="NY")

foo = Foo()
foo.get_double_aa(x=2, p=2)

from examples.more_classes import Person, aaa

aaa(a={"vvv": [datetime.now()]})
