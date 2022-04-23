
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

from examples.api_example import Bar, Foo

bar = Bar(
    i=5,
    d={},
    s="xyz",
    union=[],
    any=[1, 2, "xxx"],
    x="xxxx",
    opt=11,
    xxxxxxx=3,
    state=4,
    dob=None,
    person=1
)


foo = Foo()
foo.get_double_aa(x=2, p=2)

from examples.more_classes import aaa

aaa(a={"vvv": [datetime.now()]})
