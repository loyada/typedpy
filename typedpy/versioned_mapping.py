import copy

from .mappers import Constant, Deleted
from .structures import Structure
from .fields import FunctionCall, PositiveInt


VERSION_MAPPING = "_versions_mapping"


class Versioned(Structure):
    """Marks a structure as can be deserialized from multiple versions.
       The version is expected to start with 1 and increase by 1 in every update.
       It is expected to have a class attribute of "_versions_mapping", with an ordered list
       of the mappings. The first mapping maps version 1 to 2, the second 2 to 3, etc.

    """

    version = PositiveInt


def _convert(mapped_dict: dict, mapping):
    out_dict = copy.deepcopy(mapped_dict)
    for k, v in mapping.items():
        if isinstance(v, Constant):
            out_dict[k] = v()
        if v == Deleted:
            del out_dict[k]
        elif k.endswith("._mapper"):
            field_name = k[:(len("._mapper")-1)]
            content = mapped_dict[field_name]
            if isinstance(content, list):
                out_dict[field_name] = [_convert(x, v) for x in content]
            else:
                out_dict[field_name] = _convert(content, v)

        elif isinstance(v, str):
            out_dict[k] = out_dict[v]

        elif isinstance(v, FunctionCall):
            args = [out_dict[x] for x in v.args] if v.args else [out_dict[k]]
            out_dict[k] = v.func(*args)

    return out_dict


def convert_dict(the_dict: dict, versions_mapping):
    start_version = the_dict.get("version", 1)
    mapped_dict = copy.deepcopy(the_dict)
    for mapping in versions_mapping[(start_version-1):]:
        mapped_dict = _convert(mapped_dict, mapping)
        mapped_dict["version"] += 1
        print(mapped_dict)
    return mapped_dict
