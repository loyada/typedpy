import json
from collections.abc import Mapping

from typedpy.structures import TypedField, Structure, StructMeta
from typedpy.fields import Field, Number, String, StructureReference, \
    Array, Map, ClassReference, Enum, MultiFieldWrapper, Boolean, Tuple, Set, Anything, AnyOf, AllOf, \
    OneOf, NotField, SerializableField, SizedCollection, wrap_val


def deserialize_list_like(field, content_type, value, name):
    try:
        iter(value)
    except TypeError:
        raise ValueError("{}: must be an iterable; got {}".format(name, value))

    values = []
    items = field.items
    if isinstance(items, Field):
        list_items = []
        for i, v in enumerate(value):
            item_name = "{}_{}".format(name, i)
            try:
                list_item = deserialize_single_field(items, v, item_name)
            except (ValueError, TypeError) as e:
                prefix = "" if str(e).startswith(item_name) else "{}: ".format(item_name)
                raise ValueError("{}{}".format(prefix, str(e)))
            values.append(list_item)
    else:
        for i, item in enumerate(items):
            try:
               res = deserialize_single_field(item, value[i], name)
            except (ValueError, TypeError) as e:
                raise ValueError("{}_{}: {}".format(name, i, str(e)))
            values.append(res)
        values += value[len(items):]
    return content_type(values)


def deserialize_array(array_field, value, name):
    return deserialize_list_like(array_field, list, value, name)


def deserialize_tuple(tuple_field, value, name):
    return deserialize_list_like(tuple_field, tuple, value, name)


def deserialize_set(set_field, value, name):
    return deserialize_list_like(set_field, set, value, name)


def deserialize_multifield_wrapper(field, source_val, name):
    """
    Only primitive values are supported, otherwise deserialization is ambiguous,
    since it can only be verified when the structure is instantiated
    """
    deserialized = source_val
    found_previous_match = False
    for field_option in field.get_fields():
        try:
            deserialized =  deserialize_single_field(field_option, source_val, name)
            if isinstance(field, AnyOf):
                return deserialized
            elif isinstance(field,  NotField) :
                raise ValueError("could not deserialize {}: value {} matches field {}, but must not match it".format(
                    name, wrap_val(source_val), field))
            elif isinstance(field,  OneOf)  and found_previous_match:
                raise ValueError("could not deserialize {}: value {} matches more than one match".format(
                    name, wrap_val(source_val), field))
            found_previous_match = True
        except Exception as e:
            if isinstance(field, AllOf):
                raise ValueError("could not deserialize {}: value {} did not match {}. reason: {}".format(
                    name, wrap_val(source_val), field_option, str(e)))
    return deserialized


def deserialize_map(map_field, source_val, name):
    if not isinstance(source_val, dict):
        raise TypeError("{}: expected a dict".format(name))
    if map_field.items:
        key_field, value_field = map_field.items
    else:
        key_field, value_field = None, None
    res = {}
    for key, val in source_val.items():
        res[deserialize_single_field(key_field, key, name)] = \
            deserialize_single_field(value_field, val, name)
    return res


def deserialize_single_field(field, source_val, name):
    if isinstance(field, (Number, String, Enum, Boolean)):
        field._validate(source_val)
        value = source_val
    elif isinstance(field, TypedField) and \
            getattr(field, '_ty', '') in {str, int, float} and \
            isinstance(source_val, getattr(field, '_ty', '')):
        value = source_val
    elif isinstance(field, Array):
        value = deserialize_array(field, source_val, name)
    elif isinstance(field, Tuple):
        value = deserialize_tuple(field, source_val, name)
    elif isinstance(field, Set):
        value = deserialize_set(field, source_val, name)
    elif isinstance(field, MultiFieldWrapper):
        value = deserialize_multifield_wrapper(field, source_val, name)
    elif isinstance(field, ClassReference):
        value = deserialize_structure(getattr(field, '_ty'), source_val, name)
    elif isinstance(field, StructureReference):
        value = deserialize_structure_reference(getattr(field, '_newclass'), source_val)
    elif isinstance(field, Map):
        value = deserialize_map(field, source_val, name)
    elif isinstance(field, SerializableField):
        value = field.deserialize(source_val)
    elif isinstance(field, Anything) or field is None:
        value = source_val
    else:
        raise NotImplementedError("cannot deserialize field '{}' of type {} using value {}".
                                  format(name, field.__class__.__name__, wrap_val(source_val)))
    return value


def deserialize_structure_reference(cls, the_dict: dict):
    field_by_name = dict([(k, v) for k, v in cls.__dict__.items()
                          if isinstance(v, Field) and k in the_dict])
    kwargs = dict([(k, v) for k, v in the_dict.items() if k not in cls.__dict__])
    for name, field in field_by_name.items():
        kwargs[name] = deserialize_single_field(field, the_dict[name], name)
    cls(**kwargs)
    return kwargs


def get_all_fields_by_name(cls):
    all_classes = reversed([c for c in cls.mro() if isinstance(c, StructMeta)])
    all_fields_by_name = {}
    for cl in all_classes:
        field_by_name = dict([(k, v) for k, v in cl.__dict__.items()
                              if isinstance(v, Field)])
        all_fields_by_name.update(field_by_name)
    return all_fields_by_name


def deserialize_structure(cls, the_dict, name=None):
    """
        Deserialize a dict to a Structure instance, Jackson style.
        Note the top level must be a python dict - which implies that a JSON of
        simply a number, or string, or array, is unsupported.
        `See working examples in test. <https://github.com/loyada/typedpy/tree/master/tests/test_deserialization.py>`_

        Arguments:
            cls(type):
                The target class
            the_dict(dict):
                the source dictionary
            name(str): optional
                name of the structure, used only internally, when there is a
                class reference field. Users are not supposed to use this argument.

        Returns:
            an instance of the provided :class:`Structure` deserialized
    """
    field_by_name = get_all_fields_by_name(cls)

    if not isinstance(the_dict, dict):
        props = cls.__dict__
        fields = list(field_by_name.keys())
        required = props.get('_required', fields)
        additional_props = props.get('_additionalProperties', True)
        if len(fields) == 1 and required == fields and additional_props is False:
            field_name = fields[0]
            return cls(deserialize_single_field(getattr(cls, field_name), the_dict, field_name))
        raise TypeError("{}: Expected a dictionary; Got {}".format(name, wrap_val(the_dict)))

    kwargs = dict([(k, v) for k, v in the_dict.items() if k not in field_by_name])
    for key, field in field_by_name.items():
        if key in the_dict:
            kwargs[key] = deserialize_single_field(field, the_dict[key], key)
    return cls(**kwargs)


def serialize_val(field_definition, name, val):
    if isinstance(field_definition, SerializableField) and isinstance(field_definition, Field):
        return field_definition.serialize(val)
    if isinstance(val, (int, str, bool, float)) or val is None:
        return val
    if isinstance(field_definition, SizedCollection):
        if isinstance(field_definition, Map):
            if not isinstance(val, Mapping):
                raise TypeError("{} Expected a Mapping", name)
            if isinstance(field_definition.items, list) and len(field_definition.items)==2:
                key_type, value_type = field_definition.items
                return {serialize_val(key_type, name, k):serialize_val(value_type, name, v) for (k,v) in val.items()}
            else:
                return val
        if isinstance(field_definition.items, list):
            return [serialize_val(field_definition.items[ind], name, v) for ind,v in enumerate(val)]
        elif isinstance(field_definition.items, Field):
            return [serialize_val(field_definition.items, name, i) for i in val]
        else:
            return [serialize_val(None, name, i) for i in val]
    if isinstance(val, (list, set, tuple)):
        return [serialize_val(None, name, i) for i in val]
    if isinstance(field_definition, Anything):
        if isinstance(val, Structure):
            return serialize(val)
        elif isinstance(val, Field):
            return serialize_val(None, name, val)
    if isinstance(val, Structure) or isinstance(field_definition, Field):
        return serialize(val)
    # nothing worked. Not a typedpy field. Last ditch effort.
    try:
        return json.dumps(val)
    except Exception as ex:
        raise ValueError(f"{name}: cannot serialize value: {ex}")


def serialize(structure, compact=False):
    """
    Serialize an instance of :class:`Structure` to a JSON-like dict.
    `See working examples in test. <https://github.com/loyada/typedpy/tree/master/tests/test_serialization.py>`_

    Arguments:
        structure(:class:`Structure`):
            the structure instance to be serialized to JSON

        compact(bool):
             whether to use a compact form for Structure that is a simple wrapper of a field.
             for example: if a Structure has only one field of an int, if compact is True
             it will serialize the structure as an int instead of a dictionary

    Returns:
        a serialized Python dict
    """
    items = structure.items() if isinstance(structure, dict) \
        else [(k, v) for (k, v) in structure.__dict__.items() if k != '_instantiated']
    props = structure.__class__.__dict__
    fields = [key for key, val in props.items() if isinstance(val, Field)]
    required = props.get('_required', fields)
    additional_props = props.get('_additionalProperties', True)
    if len(fields) == 1 and required == fields \
            and additional_props is False and compact:
        key = fields[0]
        result = serialize_val(props.get(key, None), key, getattr(structure, key))
    else:
        result = {}
        for key, val in items:
            if val is None:
                continue
            result[key] = serialize_val(props.get(key, None), key, val)
    return result
