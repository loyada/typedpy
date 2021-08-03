import copy

from typedpy import Array, FunctionCall, ImmutableStructure, Integer, Map, PositiveInt, String, Structure
from typedpy.mappers import Constant, Deleted


class Bar(ImmutableStructure):
    a: Array[Integer]
    s: String


class Versioned(Structure):
    version = PositiveInt


class Foo(ImmutableStructure):
    bar: Bar
    i: Integer
    j: Integer
    m: Map[String, String]


_versions_mapping = [
        {
            "j": Constant(100),
            "old_bar._mapper": {
                "a": FunctionCall(func=lambda x: [i * 2 for i in x], args=["a"]),
            },
            "old_m": Constant({"abc": "xyz"})
        },

        {
            "old_bar._mapper": {
                "s": "sss",
                "sss": Deleted
            },
            "bar": "old_bar",
            "m": "old_m",
            "old_m": Deleted,
            "old_bar": Deleted,
        },

        {
            "i": FunctionCall(func=lambda x: x * 100, args=["i"])
        }

]



# foo_4 = Foo(
#   version=4,
#   bar=Bar(
#       a=[10, 16, 4],
#       s="john"
#   ),
#   i=200,
#   j=100,
#   m={"a": "aa", "b": "bb"}
# )
#
# foo_3 = Foo(
#     version=3,
#     bar=Bar(
#         a=[10, 16, 4],
#         s="john"
#     ),
#     i=2,
#     j=100,
#     m={"a": "aa", "b": "bb"}
# )

#
# foo_2 = Foo(
#     version=2,
#     old_bar=Bar(
#         a=[10, 16, 4],
#         sss="john"
#     ),
#     i=2,
#     j=100,
#     m={"a": "aa", "b": "bb"}
# )
#
# foo_1 = Foo(
#     version=1,
#     old_bar=Bar(
#         a=[5, 8, 2],
#         sss="john"
#     ),
#     i=2,
#     old_m={"a": "aa", "b": "bb"}
# )
#


def convert(mapped_dict: dict, mapping):
    out_dict = copy.deepcopy(mapped_dict)
    for k,v in mapping.items():
        if isinstance(v, Constant):
            out_dict[k] = v()
        if v==Deleted:
            del out_dict[k]
        elif k.endswith("._mapper"):
            field_name = k[:(len("._mapper")-1)]
            content = mapped_dict[field_name]
            if isinstance(content, list):
                out_dict[field_name] = [convert(x, v) for x in content]
            else:
                out_dict[field_name] = convert(content, v)

        elif isinstance(v, str):
            out_dict[k] = out_dict[v]

        elif isinstance(v, FunctionCall):
            args = [out_dict[x] for x in v.args] if v.args else [out_dict[k]]
            out_dict[k] = v.func(*args)

    return out_dict


def convert_dict(the_dict: dict, versions_mapping):
    start_version = the_dict.get("_version", 1)
    mapped_dict = copy.deepcopy(the_dict)
    for mapping in versions_mapping[(start_version-1):]:
        mapped_dict = convert(mapped_dict, mapping)
        mapped_dict["_version"] += 1
        print(mapped_dict)
    return mapped_dict

in_version_1 = {
    "_version": 1,
    "old_bar": {
        "a": [5,8,2],
        "sss": "john",
    },
    "i": 2,
    "old_m": {"a": "aa", "b": "bb"}
}

in_version_2 = {
    "_version": 2,
    "old_bar": {
        "a": [10, 16, 4],
        "sss": "john",
    },
    "i": 2,
    "j": 150,
    "old_m": {"abc": "xyzxyzxyzyxyzxyzxyzxz", "b": "bb"}
}


def test_version_conversion():
    x = convert_dict(in_version_1, _versions_mapping)
    print(f"version 1: {x}")
    x = convert_dict(in_version_2, _versions_mapping)
    print(f"version 2: {x}")
