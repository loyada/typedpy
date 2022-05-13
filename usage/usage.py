from examples.api_example import Bar, Foo
from examples.enums import State
from examples.generic_stuff import func, Stack

# s: str,
# person: Person,
# dob: datetime,
# union: Union[int, str],
# any: Any,
# x: int,
# state: State,
# d: Optional[dict[str, int]] = None,
# opt: Optional[float] = None,

# state: State = State.NY
# print(state.value)
# bar: Bar = Bar()
# print(bar.person1 )


# bar.i.append(4)
#
# bar = Bar(
#     i='5',
#     d=3,
#     s="xyz",
#     union=[],
#     any=[1, 2, "xxx"],
#     x="xxxx",
#     opt=11,
#     xxxxxxx=3,
#     state=State.NY,
#     dob=234,
#     person = 3,
#     arr=123,
# )
#
# foo = Foo(a={1, 2})
# foo.get_double_aa(x=2, p=2)

func(Stack[int])
