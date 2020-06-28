import collections
import json
from collections.abc import Mapping
from functools import reduce

from typedpy.structures import TypedField, Structure, StructMeta
from typedpy.fields import Field, Number, String, StructureReference, \
    Array, Map, ClassReference, Enum, MultiFieldWrapper, Boolean, Tuple, Set, Anything, AnyOf, AllOf, \
    OneOf, NotField, SerializableField, SizedCollection, wrap_val, Function


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
            deserialized = deserialize_single_field(field_option, source_val, name)
            if isinstance(field, AnyOf):
                return deserialized
            elif isinstance(field, NotField):
                raise ValueError("could not deserialize {}: value {} matches field {}, but must not match it".format(
                    name, wrap_val(source_val), field))
            elif isinstance(field, OneOf) and found_previous_match:
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
        raise TypeError("{}: expected a dict. Got {}".format(name, wrap_val(source_val)))
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
        value = deserialize_structure_internal(getattr(field, '_ty'), source_val, name)
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


class FunctionCall(Structure):
    """
    Structure that represents a function call for the purpose of serialization mappers: \
    Includes the function to be called, and a list of positional string arguments.
    """
    func = Function
    args = Array[String]
    _required = ['func']


def deserialize_structure_internal(cls, the_dict, name=None, *, mapper=None, keep_undefined=False):
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
            mapper(dict): optional
                a dict of attribute name of attribute to key in the input
            name(str): optional
                name of the structure, used only internally, when there is a
                class reference field. Users are not supposed to use this argument.
            keep_undefined(bool): optional
                should it create attributes for keys that don't appear in the class? default is False.

        Returns:
            an instance of the provided :class:`Structure` deserialized
    """
    if mapper is None:
        mapper = {}
    if not isinstance(mapper, (collections.Mapping,)):
        raise TypeError("Mapper must be a mapping")
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

    kwargs = dict([(k, v) for k, v in the_dict.items() if k not in field_by_name and keep_undefined])
    for key, field in field_by_name.items():
        process = False
        if key in the_dict and key not in mapper:
            processed_input = the_dict[key]
            process = True
        elif key in mapper:
            processed_input = get_processed_input(key, mapper, the_dict)
            process = True
        if process:
            kwargs[key] = deserialize_single_field(field, processed_input, key)

    return cls(**kwargs)


def deserialize_structure(cls, the_dict, *, mapper=None, keep_undefined=True):
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
            mapper(dict): optional
                the key is the target attribute name. The value can either be a path of the value in the source dict
                using dot notation, for example: "aaa.bbb", or a :class:`FunctionCall`. In the latter case,
                the function is the used to preprocess the input prior to deserialization/validation.
                The args attribute in the function call is optional. If non provided, the input to the function is
                the value with the same key. Otherwise it is the keys of the values in the input that are injected
                to the provided function. See working examples in the tests link above.
            keep_undefined(bool): optional
                should it create attributes for keys that don't appear in the class? default is True.

        Returns:
            an instance of the provided :class:`Structure` deserialized
    """
    return deserialize_structure_internal(cls, the_dict, mapper=mapper, keep_undefined=keep_undefined)


def _deep_get(dictionary, deep_key):
    keys = deep_key.split('.')
    return reduce(lambda d, key: d.get(key) if d else None, keys, dictionary)


def get_processed_input(key, mapper, the_dict):
    if key in mapper:
        key_mapper = mapper[key]
        if isinstance(key_mapper, (FunctionCall,)):
            args = [_deep_get(the_dict, k) for k in key_mapper.args] if key_mapper.args else [the_dict.get(key)]
            processed_input = key_mapper.func(*args)
        elif isinstance(key_mapper, (str,)):
            processed_input = _deep_get(the_dict, key_mapper)
        else:
            raise TypeError("mapper value must be a key in the input or a FunctionCal. Got {}".format(wrap_val(key_mapper)))
    else:
        processed_input = the_dict[key]
    return processed_input


def serialize_val(field_definition, name, val):
    if isinstance(field_definition, SerializableField) and isinstance(field_definition, Field):
        return field_definition.serialize(val)
    if isinstance(val, (int, str, bool, float)) or val is None:
        return val
    if isinstance(field_definition, SizedCollection):
        if isinstance(field_definition, Map):
            if not isinstance(val, Mapping):
                raise TypeError("{} Expected a Mapping", name)
            if isinstance(field_definition.items, list) and len(field_definition.items) == 2:
                key_type, value_type = field_definition.items
                return {serialize_val(key_type, name, k): serialize_val(value_type, name, v) for (k, v) in val.items()}
            else:
                return val
        if isinstance(field_definition.items, list):
            return [serialize_val(field_definition.items[ind], name, v) for ind, v in enumerate(val)]
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
        return serialize_internal(val)
    # nothing worked. Not a typedpy field. Last ditch effort.
    try:
        return json.loads(json.dumps(val))
    except Exception as ex:
        raise ValueError(f"{name}: cannot serialize value: {ex}")


def serialize_field(field_definition: Field, value):
    """
    Serialize a specific :class:`Field` from a structure to a JSON-like dict.
    Example:

            .. code-block:: python

                class Foo(Structure):
                    a = String
                    i = Integer

                class Bar(Structure):
                    x = Float
                    foos = Array[Foo]

                bar = Bar(x=0.5, foos=[Foo(a='a', i=5), Foo(a='b', i=1)])
                assert serialize_field(Bar.foos, bar.foos)[0]['a'] == 'a'


    Arguments:
        field_definition(:class:`Field`):
           the field definition

        value:
             the value of the field to deserialize

    Returns:
        a serialized Python object that can be directly converted to JSON
    """
    return serialize_val(field_definition, field_definition._name, value)


def _get_mapped_value(mapper, key, items):
    if key in mapper:
        key_mapper = mapper[key]
        if isinstance(key_mapper, (FunctionCall,)):
            args = [items.get(k) for k in key_mapper.args] if key_mapper.args else [items.get(key)]
            return key_mapper.func(*args)
        elif not isinstance(key_mapper, (FunctionCall,str)):
            raise TypeError("mapper must have a FunctionCall or a string")

    return None


def serialize_internal(structure, mapper=None, compact=False):
    if mapper is None:
        mapper = {}
    field_by_name = get_all_fields_by_name(structure.__class__)

    items = structure.items() if isinstance(structure, dict) \
        else [(k, v) for (k, v) in structure.__dict__.items() if k != '_instantiated']
    props = structure.__class__.__dict__
    fields = list(field_by_name.keys())
    required = props.get('_required', fields)
    additional_props = props.get('_additionalProperties', True)
    if len(fields) == 1 and required == fields \
            and additional_props is False and compact:
        key = fields[0]
        result = serialize_val(field_by_name.get(key, None), key, getattr(structure, key))
    else:
        result = {}
        items_map = dict(items)
        for key, val in items:
            if val is None:
                continue
            mapped_key = mapper[key] if key in mapper and isinstance(mapper[key], (str,)) else key
            mapped_value = _get_mapped_value(mapper, key, items_map)
            the_field_definition = Anything if mapped_value else field_by_name.get(key, None)
            result[mapped_key] = serialize_val(the_field_definition, key, mapped_value or val)
    return result


def serialize(structure, *, mapper=None, compact=False):
    """
    Serialize an instance of :class:`Structure` to a JSON-like dict.
    `See working examples in test. <https://github.com/loyada/typedpy/tree/master/tests/test_serialization.py>`_

    Arguments:
        structure(:class:`Structure`):
            the structure instance to be serialized to JSON

        mapper(dict): optional
             a dictionary where the key is the name of the attribute in the structure, and the value is name of the
             key to map its value to, or a :class:`FunctionCall` where the function is the transformation, and
             the args are a list of attributes that are arguments to the function. if args is empty it function transform
             the current attribute.
        compact(bool):
             whether to use a compact form for Structure that is a simple wrapper of a field.
             for example: if a Structure has only one field of an int, if compact is True
             it will serialize the structure as an int instead of a dictionary

    Returns:
        a serialized Python object that can be directly converted to JSON
        :param compact: in case there is a single attribute, it does not wrap it with a dictionary
        :param structure: an instance of :class:`Structure`
        :param mapper: a dict with the new key, by the attribute name
    """
    if mapper is None:
        mapper = {}
    if not isinstance(mapper, (collections.Mapping,)):
        raise TypeError("Mapper must be a mapping")
    if not isinstance(structure, Structure):
        raise TypeError("serialize: must get a Structure. Got: {}".format(structure))
    return serialize_internal(structure, mapper=mapper, compact=compact)
