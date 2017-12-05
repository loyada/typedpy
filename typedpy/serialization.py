from typedpy import Field, Number, String, StructureReference, Array, Map, Integer, Float, ClassReference, Enum, AnyOf, \
    OneOf, AllOf, NotField, Structure
from typedpy.fields import MultiFieldWrapper, Boolean


def deserialize_array(array_field, value, name):
    if not isinstance(value, list):
        return value
    items = array_field.items
    if isinstance(items, Field):
         [deserialize_single_field(items, v) for v in value]
    else:
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
            raise NotImplementedError("{} deserialization only supports Number, " +
                                      "String and Enum".format(name))
    return source_val


def deserialize_single_field(field, source_val, name):
    if isinstance(field, (Number, String, Map, Enum)):
        value = source_val
    elif isinstance(field, Array):
        value = deserialize_array(field, source_val, name)
    elif isinstance(field, MultiFieldWrapper):
        value = deserialize_multifield_wrapper(field, source_val, name)
    elif isinstance(field, ClassReference):
        value = deserialize_structure(field._ty, source_val)
    elif isinstance(field, StructureReference):
        value = deserialize_structure_reference(field._newclass, source_val)
    else:
        raise NotImplementedError("cannot deserialize field '{}'".format(name))
    return value

def deserialize_structure_reference(cls, the_dict: dict):
    field_by_name = dict([(k, v) for k,v in cls.__dict__.items() if isinstance(v, Field) and k in the_dict])
    kwargs = dict([(k, v) for k,v in the_dict.items() if k not in cls.__dict__])
    for name, field in field_by_name.items():
        kwargs[name] = deserialize_single_field(field, the_dict[name], name)
    return kwargs


def deserialize_structure(cls, the_dict: dict):
    field_by_name = dict([(k, v) for k,v in cls.__dict__.items() if isinstance(v, Field) and k in the_dict])
    kwargs = dict([(k, v) for k,v in the_dict.items() if k not in cls.__dict__])
    for name, field in field_by_name.items():
        kwargs[name] = deserialize_single_field(field, the_dict[name], name)
    return cls(**kwargs)




