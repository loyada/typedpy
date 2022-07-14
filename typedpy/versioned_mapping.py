import copy

from .commons import Constant, deep_get
from .mappers import Deleted
from .structures import Structure
from .fields import FunctionCall, PositiveInt


VERSION_MAPPING = "_versions_mapping"


class Versioned(Structure):
    """
    Marks a structure as can be deserialized from multiple versions.
    The version is expected to start with 1 and increase by 1 in every update.
    It is expected to have a class attribute of "_versions_mapping", with an ordered list
    of the mappings. The first mapping maps version 1 to 2, the second 2 to 3, etc.

    Arguments:

    _versions_mapping: optional
        An array of mappers that outlines how to convert older versions to the latest version.

    """

    version: PositiveInt

    def __init__(self, *args, **kwargs):
        versions_mapping = getattr(self, VERSION_MAPPING, [])
        default_version = len(versions_mapping) + 1
        kwargs["version"] = default_version
        super().__init__(*args, **kwargs)


def _convert(mapped_dict: dict, mapping):
    out_dict = copy.deepcopy(mapped_dict)
    for k, v in mapping.items():
        if isinstance(v, Constant):
            out_dict[k] = v()
        elif k.endswith("._mapper"):
            field_name = k[: -len("._mapper")]
            content = mapped_dict.get(field_name, None)
            if content is not None:
                if isinstance(content, list):
                    out_dict[field_name] = [_convert(x, v) for x in content]
                else:
                    out_dict[field_name] = _convert(content, v)

        elif isinstance(v, FunctionCall):
            args = [out_dict.get(x) for x in v.args] if v.args else [out_dict.get(k)]
            out_dict[k] = v.func(*args)

    for k, v in mapping.items():
        if isinstance(v, str):
            out_dict[k] = deep_get(out_dict, v)

    for k, v in mapping.items():
        if v == Deleted and k in out_dict:
            del out_dict[k]
    return out_dict


def convert_dict(the_dict: dict, versions_mapping):
    start_version = the_dict.get("version", 1)
    mapped_dict = copy.deepcopy(the_dict)
    for mapping in versions_mapping[(start_version - 1) :]:
        mapped_dict = _convert(mapped_dict, mapping)
        mapped_dict["version"] = mapped_dict.get("version", 0) + 1
    return mapped_dict
