from .api_example import Bar

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
from .enums import State

bar = Bar(
    i=5,
    d={},
    s="xyz",
    union=[],
    any=[1, 2, "xxx"],
    x="xxxx",
    opt=11,
    xxxxxxx=3,
    state=State.NY,
)
