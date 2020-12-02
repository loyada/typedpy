import collections
import enum
import json
from functools import reduce
from typing import Dict

from typedpy.fields import _ListStruct, Deque
from typedpy.structures import (
    TypedField,
    Structure,
    _get_all_fields_by_name,
    ADDITIONAL_PROPERTIES,
    REQUIRED_FIELDS,
)
from typedpy.fields import (
    Field,
    Number,
    String,
    StructureReference,
    Array,
    Map,
    ClassReference,
    Enum,
    MultiFieldWrapper,
    Boolean,
    Tuple,
    Set,
    Anything,
    AnyOf,
    AllOf,
    OneOf,
    NotField,
    SerializableField,
    SizedCollection,
    wrap_val,
    Function,
    _DictStruct,
)


def deserialize_list_like(
    field, content_type, value, name, *, keep_undefined=True, mapper=None
):
    if not isinstance(value, (list, tuple, set)):
        raise ValueError("{}: must be list, set, or tuple; got {}".format(name, value))

    values = []
    items = field.items
    if isinstance(items, Field):
        for i, v in enumerate(value):
            item_name = "{}_{}".format(name, i)
            try:
                list_item = deserialize_single_field(
                    items, v, item_name, keep_undefined=keep_undefined, mapper=mapper
                )
            except (ValueError, TypeError) as e:
                prefix = (
                    "" if str(e).startswith(item_name) else "{}: ".format(item_name)
                )
                raise ValueError("{}{}".format(prefix, str(e))) from e
            values.append(list_item)
    elif isinstance(items, (list, tuple)):
        for i, item in enumerate(items):
            try:
                res = deserialize_single_field(
                    item, value[i], name, keep_undefined=keep_undefined, mapper=mapper
                )
            except (ValueError, TypeError) as e:
                raise ValueError("{}_{}: {}".format(name, i, str(e))) from e
            values.append(res)
        values += value[len(items) :]
    else:
        values = value
    return content_type(values)


def deserialize_array(array_field, value, name, *, keep_undefined=True, mapper):
    return deserialize_list_like(
        array_field, list, value, name, keep_undefined=keep_undefined, mapper=mapper
    )


def deserialize_deque(array_field, value, name, *, keep_undefined=True, mapper):
    return deserialize_list_like(
        array_field, collections.deque, value, name, keep_undefined=keep_undefined, mapper=mapper
    )


def deserialize_tuple(tuple_field, value, name, *, keep_undefined=True, mapper):
    return deserialize_list_like(
        tuple_field, tuple, value, name, keep_undefined=keep_undefined, mapper=mapper
    )


def deserialize_set(set_field, value, name, *, keep_undefined=True, mapper):
    return deserialize_list_like(
        set_field, set, value, name, keep_undefined=keep_undefined, mapper=mapper
    )


def deserialize_multifield_wrapper(
    field, source_val, name, *, keep_undefined=True, mapper=None
):
    """
    Only primitive values are supported, otherwise deserialization is ambiguous,
    since it can only be verified when the structure is instantiated
    """
    deserialized = source_val
    found_previous_match = False
    for field_option in field.get_fields():
        try:
            deserialized = deserialize_single_field(
                field_option,
                source_val,
                name,
                keep_undefined=keep_undefined,
                mapper=mapper,
            )
            if isinstance(field, AnyOf):
                return deserialized
            elif isinstance(field, NotField):
                raise ValueError(
                    "could not deserialize {}: value {} matches field {}, but must not match it".format(
                        name, wrap_val(source_val), field
                    )
                )
            elif isinstance(field, OneOf) and found_previous_match:
                raise ValueError(
                    "could not deserialize {}: value {} matches more than one match".format(
                        name, wrap_val(source_val)
                    )
                )
            found_previous_match = True
        except Exception as e:
            if isinstance(field, AllOf):
                raise ValueError(
                    "could not deserialize {}: value {} did not match {}. reason: {}".format(
                        name, wrap_val(source_val), field_option, str(e)
                    )
                ) from e
    return deserialized


def deserialize_map(map_field, source_val, name):
    if not isinstance(source_val, dict):
        raise TypeError(
            "{}: expected a dict. Got {}".format(name, wrap_val(source_val))
        )
    if map_field.items:
        key_field, value_field = map_field.items
    else:
        key_field, value_field = None, None
    res = {}
    for key, val in source_val.items():
        res[deserialize_single_field(key_field, key, name)] = deserialize_single_field(
            value_field, val, name
        )
    return res


def deserialize_single_field(
    field, source_val, name, *, mapper=None, keep_undefined=True
):
    if isinstance(field, (Number, String, Enum, Boolean)):
        field._validate(source_val)
        value = source_val
    elif (
        isinstance(field, TypedField)
        and getattr(field, "_ty", "") in {str, int, float}
        and isinstance(source_val, getattr(field, "_ty", ""))
    ):
        value = source_val
    elif isinstance(field, Array):
        value = deserialize_array(
            field, source_val, name, keep_undefined=keep_undefined, mapper=mapper
        )
    elif isinstance(field, Deque):
        value = deserialize_deque(
            field, source_val, name, keep_undefined=keep_undefined, mapper=mapper
        )
    elif isinstance(field, Tuple):
        value = deserialize_tuple(
            field, source_val, name, keep_undefined=keep_undefined, mapper=mapper
        )
    elif isinstance(field, Set):
        value = deserialize_set(
            field, source_val, name, keep_undefined=keep_undefined, mapper=mapper
        )
    elif isinstance(field, MultiFieldWrapper):
        value = deserialize_multifield_wrapper(
            field, source_val, name, keep_undefined=keep_undefined, mapper=mapper
        )
    elif isinstance(field, ClassReference):
        value = deserialize_structure_internal(
            getattr(field, "_ty"),
            source_val,
            name,
            keep_undefined=keep_undefined,
            mapper=mapper,
        )
    elif isinstance(field, StructureReference):
        value = deserialize_structure_reference(
            getattr(field, "_newclass"),
            source_val,
            keep_undefined=keep_undefined,
            mapper=mapper,
        )
    elif isinstance(field, Map):
        value = deserialize_map(field, source_val, name)
    elif isinstance(field, SerializableField):
        value = field.deserialize(source_val)
    elif isinstance(field, Anything) or field is None:
        value = source_val
    elif isinstance(field, TypedField) and isinstance(source_val, (list, dict)):
        ty = getattr(field, "_ty")
        if isinstance(source_val, list):
            value = ty(*source_val)
        elif isinstance(source_val, dict):
            value = ty(**source_val)
    else:
        raise NotImplementedError(
            "cannot deserialize field '{}' of type {} using value {}. Are you using non-Typepy class?".format(
                name, field.__class__.__name__, wrap_val(source_val)
            )
        )
    return value


def deserialize_structure_reference(cls, the_dict: dict, *, keep_undefined, mapper):
    field_by_name = {k: v for k, v in cls.__dict__.items() if isinstance(v, Field)}
    kwargs = dict(
        [
            (k, v)
            for k, v in the_dict.items()
            if k not in field_by_name and keep_undefined
        ]
    )

    kwargs.update(construct_fields_map(field_by_name, keep_undefined, mapper, the_dict))
    cls(**kwargs)
    return kwargs


def construct_fields_map(field_by_name, keep_undefined, mapper, the_dict):
    result = {}
    for key, field in field_by_name.items():
        process = False
        processed_input = None
        if key in the_dict and key not in mapper:
            processed_input = the_dict[key]
            process = True
        elif key in mapper:
            processed_input = get_processed_input(key, mapper, the_dict)
            process = True
        if process:
            sub_mapper = mapper.get(f"{key}._mapper", {})
            result[key] = deserialize_single_field(
                field,
                processed_input,
                key,
                mapper=sub_mapper,
                keep_undefined=keep_undefined,
            )
    return result


class FunctionCall(Structure):
    """
    Structure that represents a function call for the purpose of serialization mappers: \
    Includes the function to be called, and a list of keys of positional string arguments.
    This is not a generic function call.

    Arguments:
        func(Function):
            the function to be called. Note this must be a real function, not any callable.
        args(Array[String]): optional
            the keys of the arguments to be used as positional arguments for the function call
    """

    func = Function
    args = Array[String]
    _required = ["func"]


def deserialize_structure_internal(
    cls, the_dict, name=None, *, mapper=None, keep_undefined=True
):
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
    if not isinstance(mapper, (collections.abc.Mapping,)):
        raise TypeError("Mapper must be a mapping")
    field_by_name = _get_all_fields_by_name(cls)

    if not isinstance(the_dict, dict):
        props = cls.__dict__
        fields = list(field_by_name.keys())
        required = props.get(REQUIRED_FIELDS, fields)
        additional_props = props.get(ADDITIONAL_PROPERTIES, True)
        if len(fields) == 1 and required == fields and additional_props is False:
            field_name = fields[0]
            return cls(
                deserialize_single_field(getattr(cls, field_name), the_dict, field_name)
            )
        raise TypeError(
            "{}: Expected a dictionary; Got {}".format(name, wrap_val(the_dict))
        )

    kwargs = dict(
        [
            (k, v)
            for k, v in the_dict.items()
            if k not in field_by_name and keep_undefined
        ]
    )
    kwargs.update(construct_fields_map(field_by_name, keep_undefined, mapper, the_dict))

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
    return deserialize_structure_internal(
        cls, the_dict, mapper=mapper, keep_undefined=keep_undefined
    )


def _deep_get(dictionary, deep_key):
    keys = deep_key.split(".")
    return reduce(lambda d, key: d.get(key) if d else None, keys, dictionary)


def get_processed_input(key, mapper, the_dict):
    key_mapper = mapper[key]
    if isinstance(key_mapper, (FunctionCall,)):
        args = (
            [_deep_get(the_dict, k) for k in key_mapper.args]
            if key_mapper.args
            else [the_dict.get(key)]
        )
        processed_input = key_mapper.func(*args)
    elif isinstance(key_mapper, (str,)):
        processed_input = _deep_get(the_dict, key_mapper)
    else:
        raise TypeError(
            "mapper value must be a key in the input or a FunctionCal. Got {}".format(
                wrap_val(key_mapper)
            )
        )
    return processed_input


def serialize_val(field_definition, name, val, mapper=None):
    if isinstance(field_definition, SerializableField) and isinstance(
        field_definition, Field
    ):
        return field_definition.serialize(val)
    if isinstance(val, (int, str, bool, float)) or val is None:
        return val
    if isinstance(val, (enum.Enum,)):
        return val.name
    if isinstance(field_definition, SizedCollection):
        if isinstance(field_definition, Map):
            if (
                isinstance(field_definition.items, list)
                and len(field_definition.items) == 2
            ):
                key_type, value_type = field_definition.items
                return {
                    serialize_val(key_type, name, k): serialize_val(value_type, name, v)
                    for (k, v) in val.items()
                }
            else:
                return {
                    serialize_val(Anything, name, k): serialize_val(Anything, name, v)
                    for (k, v) in val.items()
                }
        if isinstance(field_definition.items, list):
            return [
                serialize_val(field_definition.items[ind], name, v, mapper=mapper)
                for ind, v in enumerate(val)
            ]
        elif isinstance(field_definition.items, Field):
            return [
                serialize_val(field_definition.items, name, i, mapper=mapper)
                for i in val
            ]
        else:
            return [serialize_val(None, name, i, mapper=mapper) for i in val]
    if isinstance(val, (list, set, tuple)):
        return [serialize_val(None, name, i) for i in val]
    if isinstance(field_definition, Anything) and isinstance(val, Structure):
        return serialize(val, mapper=mapper)
    if isinstance(val, Structure) or isinstance(field_definition, Field):
        return serialize_internal(val, mapper=mapper)

    # nothing worked. Not a typedpy field. Last ditch effort.
    try:
        return json.loads(json.dumps(val))
    except Exception as ex:
        raise ValueError(f"{name}: cannot serialize value: {ex}") from ex


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
            args = (
                [items.get(k) for k in key_mapper.args]
                if key_mapper.args
                else [items.get(key)]
            )
            return key_mapper.func(*args)
        elif not isinstance(key_mapper, (FunctionCall, str)):
            raise TypeError("mapper must have a FunctionCall or a string")

    return None


def serialize_internal(structure, mapper=None, compact=False):
    if mapper is None:
        mapper = {}
    field_by_name = _get_all_fields_by_name(structure.__class__)

    items = (
        structure.items()
        if isinstance(structure, dict)
        else [(k, v) for (k, v) in structure.__dict__.items() if k != "_instantiated"]
    )
    props = structure.__class__.__dict__
    fields = list(field_by_name.keys())
    additional_props = props.get(ADDITIONAL_PROPERTIES, True)
    if (
        len(fields) == 1
        and props.get(REQUIRED_FIELDS, fields) == fields
        and additional_props is False
        and compact
    ):
        key = fields[0]
        result = serialize_val(
            field_by_name.get(key, None), key, getattr(structure, key)
        )
    else:
        result = {}
        items_map = dict(items)
        for key, val in items:
            if val is None:
                continue
            mapped_key = (
                mapper[key]
                if key in mapper and isinstance(mapper[key], (str,))
                else key
            )
            mapped_value = _get_mapped_value(mapper, key, items_map)
            the_field_definition = (
                Anything if mapped_value else field_by_name.get(key, None)
            )
            sub_mapper = mapper.get(f"{key}._mapper", {})
            result[mapped_key] = serialize_val(
                the_field_definition, key, mapped_value or val, mapper=sub_mapper
            )
    return result


def serialize(value, *, mapper: Dict = None, compact=False):
    """
    Serialize an instance of :class:`Structure` to a JSON-like dict.
    `See working examples in test. <https://github.com/loyada/typedpy/tree/master/tests/test_serialization.py>`_

    Arguments:
        value(:class:`Structure` or a field value with an obvious serialization):
            The value to be serialized - a structure instance, or a field value for which typedpy can deduce the
             serialization.
            In the general case, if you just need to serialize a field value, it's better to use serialize_field().

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
    if not isinstance(mapper, (collections.abc.Mapping,)):
        raise TypeError("Mapper must be a mapping")
    if not isinstance(value, (Structure, StructureReference)):
        if value is None or isinstance(value, (int, str, bool, float)):
            return value
        if isinstance(value, (_ListStruct, _DictStruct)):
            field_definition = value._field_definition
            return serialize_val(field_definition, field_definition._name, value)
        if isinstance(value, (enum.Enum,)):
            return value.name
        raise TypeError(
            "serialize: Not a Structure or Field that with an obvious serialization. Got: {}."
            " Maybe try serialize_field() instead?".format(value)
        )
    return serialize_internal(value, mapper=mapper, compact=compact)
