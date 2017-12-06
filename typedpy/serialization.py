from typedpy import Structure
from typedpy.fields import Field, Number, String, StructureReference,\
    Array, Map, ClassReference, Enum, MultiFieldWrapper, Boolean


def deserialize_array(array_field, value, name):
    if not isinstance(value, list):
        return value
    items = array_field.items
    if isinstance(items, Field):
        return [deserialize_single_field(items, v, name) for v in value]

    values = []
    for i, field in enumerate(items):
        res = deserialize_single_field(field, value[i], name)
        values.append(res)
    values += value[len(items):]
    return values


def deserialize_multifield_wrapper(field, source_val, name):
    """
    Only primitive values are supported, otherwise deserialization is ambiguous,
    since it can only be verified when the structure is instantiated
    """
    for field_option in field.get_fields():
        if not isinstance(field_option, (Number, String, Enum, Boolean)):
            raise NotImplementedError("{}: deserialization only supports Number, ".format(name) +
                                      "String and Enum")
    return source_val


def deserialize_map(map_field, source_val, name):
    if not isinstance(source_val, dict):
        return source_val


def deserialize_single_field(field, source_val, name):
    if isinstance(field, (Number, String, Map, Enum, Boolean)):
        value = source_val
    elif isinstance(field, Array):
        value = deserialize_array(field, source_val, name)
    elif isinstance(field, MultiFieldWrapper):
        value = deserialize_multifield_wrapper(field, source_val, name)
    elif isinstance(field, ClassReference):
        value = deserialize_structure(getattr(field, '_ty'), source_val, name)
    elif isinstance(field, StructureReference):
        value = deserialize_structure_reference(getattr(field, '_newclass'), source_val)
    elif isinstance(field, Map):
        value = deserialize_map(field, source_val, name)
    else:
        raise NotImplementedError("cannot deserialize field '{}'".format(name))
    return value

def deserialize_structure_reference(cls, the_dict: dict):
    field_by_name = dict([(k, v) for k, v in cls.__dict__.items()
                          if isinstance(v, Field) and k in the_dict])
    kwargs = dict([(k, v) for k, v in the_dict.items() if k not in cls.__dict__])
    for name, field in field_by_name.items():
        kwargs[name] = deserialize_single_field(field, the_dict[name], name)
    return kwargs


def deserialize_structure(cls, the_dict, name=None):
    """
       Deserialize a dict to a Structure instance, Jackson style.
       There are certain limitations to what is supported.
        `See working example in test.
         <https://github.com/loyada/typedpy/tree/master/tests/test_deserialization.py>`_

      Arguments:
          cls(type):
            The target class
          the_dict(dict):
              the source dictionary
          name(str): optional
              name of the structure, used only internally, when there is a
              class reference field. Users are not supposed to use it.
    """
    if not isinstance(the_dict, dict):
        raise TypeError("{}: Expected a dictionary".format(name))
    field_by_name = dict([(k, v) for k, v in cls.__dict__.items()
                          if isinstance(v, Field) and k in the_dict])
    kwargs = dict([(k, v) for k, v in the_dict.items() if k not in cls.__dict__])
    for key, field in field_by_name.items():
        kwargs[key] = deserialize_single_field(field, the_dict[key], key)
    return cls(**kwargs)


def serialize_val(name, val):
    if isinstance(val, (set, tuple)):
        raise TypeError("{}: Serialization unsupported for set, tuple".format(name))
    if isinstance(val, (int, str, bool, float)) or val is None:
        return val
    elif isinstance(val, list):
        return [serialize_val(name, i) for i in val]
    else:
        return serialize(val)



def serialize(structure):
    items = structure.items() if isinstance(structure, dict) \
        else structure.__dict__.items()
    result = {}
    for key, val in items:
        if val is None:
            continue
        result[key] = serialize_val(key, val)
    return result
