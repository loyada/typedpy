import collections
import enum
import json
from collections import Mapping
from functools import reduce
from typing import Dict

from .versioned_mapping import VERSION_MAPPING, Versioned, convert_dict
from .mappers import (
    aggregate_deserialization_mappers,
    aggregate_serialization_mappers,
    mappers,
)
from .structures import (
    TypedField,
    Structure,
    _get_all_fields_by_name,
    ADDITIONAL_PROPERTIES,
    REQUIRED_FIELDS,
    IGNORE_NONE_VALUES,
    NoneField,
)
from .fields import (
    Field,
    FunctionCall,
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
    _ListStruct,
    Deque,
    Generator,
)


# pylint: disable=too-many-locals, too-many-arguments, too-many-branches


def deserialize_list_like(
        field,
        content_type,
        value,
        name,
        *,
        keep_undefined=True,
        mapper=None,
        camel_case_convert=False,
):
    if not isinstance(value, (list, tuple, set)):
        raise ValueError(
            "{}: Got {}; Expected a list, set, or tuple".format(name, value)
        )

    values = []
    items = field.items
    if isinstance(items, Field):
        ignore_none = getattr(items, IGNORE_NONE_VALUES, False)
        for i, v in enumerate(value):
            item_name = "{}_{}".format(name, i)
            try:
                list_item = deserialize_single_field(
                    items,
                    v,
                    item_name,
                    keep_undefined=keep_undefined,
                    mapper=mapper,
                    camel_case_convert=camel_case_convert,
                    ignore_none=ignore_none,
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
                ignore_none = getattr(item, IGNORE_NONE_VALUES, False)
                res = deserialize_single_field(
                    item,
                    value[i],
                    name,
                    keep_undefined=keep_undefined,
                    mapper=mapper,
                    camel_case_convert=camel_case_convert,
                    ignore_none=ignore_none,
                )
            except (ValueError, TypeError) as e:
                raise ValueError("{}_{}: {}".format(name, i, str(e))) from e
            values.append(res)
        values += value[len(items):]
    else:
        values = value
    return content_type(values)


def deserialize_array(
        array_field, value, name, *, keep_undefined=True, mapper, camel_case_convert=False
):
    return deserialize_list_like(
        array_field,
        list,
        value,
        name,
        keep_undefined=keep_undefined,
        mapper=mapper,
        camel_case_convert=camel_case_convert,
    )


def deserialize_deque(
        array_field, value, name, *, keep_undefined=True, mapper, camel_case_convert=False
):
    return deserialize_list_like(
        array_field,
        collections.deque,
        value,
        name,
        keep_undefined=keep_undefined,
        mapper=mapper,
        camel_case_convert=camel_case_convert,
    )


def deserialize_tuple(
        tuple_field, value, name, *, keep_undefined=True, mapper, camel_case_convert=False
):
    return deserialize_list_like(
        tuple_field,
        tuple,
        value,
        name,
        keep_undefined=keep_undefined,
        mapper=mapper,
        camel_case_convert=camel_case_convert,
    )


def deserialize_set(
        set_field, value, name, *, keep_undefined=True, mapper, camel_case_convert=False
):
    return deserialize_list_like(
        set_field,
        set,
        value,
        name,
        keep_undefined=keep_undefined,
        mapper=mapper,
        camel_case_convert=camel_case_convert,
    )


def deserialize_multifield_wrapper(
        field,
        source_val,
        name,
        *,
        keep_undefined=True,
        mapper=None,
        camel_case_convert=False,
):
    """
    Only primitive values are supported, otherwise deserialization is ambiguous,
    since it can only be verified when the structure is instantiated
    """
    deserialized = source_val
    found_previous_match = False
    failures = 0
    err_messages = []
    for field_option in field.get_fields():
        try:
            ignore_none = getattr(field_option, IGNORE_NONE_VALUES, False)

            deserialized = deserialize_single_field(
                field_option,
                source_val,
                name,
                keep_undefined=keep_undefined,
                mapper=mapper,
                camel_case_convert=camel_case_convert,
                ignore_none=ignore_none,
            )
            if isinstance(field, AnyOf):
                return deserialized
            elif isinstance(field, NotField):
                raise ValueError(
                    "{}: Got {}; Matches field {}, but must not match it".format(
                        name, wrap_val(source_val), field
                    )
                )
            elif isinstance(field, OneOf) and found_previous_match:
                raise ValueError(
                    "{}: Got {}; Matches more than one match".format(
                        name, wrap_val(source_val)
                    )
                )
            found_previous_match = True
        except Exception as e:
            failures += 1
            err_messages.append(
                "({}) Does not match {}. reason: {}".format(
                    len(err_messages) + 1, field_option, str(e)
                )
            )
            if isinstance(field, AllOf):
                raise ValueError(
                    "{}: Got {}; Does not match {}. reason: {}".format(
                        name, wrap_val(source_val), field_option, str(e)
                    )
                ) from e
    if failures == len(field.get_fields()) and not isinstance(field, NotField):
        raise ValueError(
            "{}: Got {}; Does not match any field option: {}".format(
                name, wrap_val(source_val), ". ".join(err_messages)
            )
        )
    return deserialized


def deserialize_map(map_field, source_val, name, camel_case_convert=False):
    if not isinstance(source_val, dict):
        raise TypeError(
            "{}: Got {}; Expected a dictionary".format(name, wrap_val(source_val))
        )
    if map_field.items:
        key_field, value_field = map_field.items
    else:
        key_field, value_field = None, None
    res = {}
    for key, val in source_val.items():
        ignore_none = getattr(value_field, IGNORE_NONE_VALUES, False)

        res[
            deserialize_single_field(
                key_field, key, name, camel_case_convert=camel_case_convert
            )
        ] = deserialize_single_field(
            value_field,
            val,
            name,
            camel_case_convert=camel_case_convert,
            ignore_none=ignore_none,
        )
    return res


def deserialize_single_field(  # pylint: disable=too-many-branches
        field,
        source_val,
        name,
        *,
        mapper=None,
        keep_undefined=True,
        camel_case_convert=False,
        ignore_none=False,
):
    if source_val is None and (ignore_none or isinstance(field, NoneField)):
        return source_val
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
            field,
            source_val,
            name,
            keep_undefined=keep_undefined,
            mapper=mapper,
            camel_case_convert=camel_case_convert,
        )
    elif isinstance(field, Deque):
        value = deserialize_deque(
            field,
            source_val,
            name,
            keep_undefined=keep_undefined,
            mapper=mapper,
            camel_case_convert=camel_case_convert,
        )
    elif isinstance(field, Tuple):
        value = deserialize_tuple(
            field,
            source_val,
            name,
            keep_undefined=keep_undefined,
            mapper=mapper,
            camel_case_convert=camel_case_convert,
        )
    elif isinstance(field, Set):
        value = deserialize_set(
            field,
            source_val,
            name,
            keep_undefined=keep_undefined,
            mapper=mapper,
            camel_case_convert=camel_case_convert,
        )
    elif isinstance(field, MultiFieldWrapper):
        value = deserialize_multifield_wrapper(
            field,
            source_val,
            name,
            keep_undefined=keep_undefined,
            mapper=mapper,
            camel_case_convert=camel_case_convert,
        )
    elif isinstance(field, ClassReference):
        value = (
            deserialize_structure_internal(
                getattr(field, "_ty", None),
                source_val,
                name,
                keep_undefined=keep_undefined,
                mapper=mapper,
                camel_case_convert=camel_case_convert,
            )
            if not isinstance(source_val, Structure)
            else source_val
        )
    elif isinstance(field, StructureReference):
        try:
            value = deserialize_structure_reference(
                getattr(field, "_newclass", None),
                source_val,
                keep_undefined=keep_undefined,
                mapper=mapper,
                camel_case_convert=camel_case_convert,
            )
        except Exception as e:
            raise ValueError(
                "{}: Got {}; {}".format(name, wrap_val(source_val), str(e))
            ) from e
    elif isinstance(field, Map):
        value = deserialize_map(
            field, source_val, name, camel_case_convert=camel_case_convert
        )
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
    elif isinstance(field, NoneField):
        raise ValueError("{}: Got {}; Expected None".format(name, wrap_val(source_val)))
    else:
        raise NotImplementedError(
            "{}: Got {}; Cannot deserialize value of type {}. Are you using non-Typepy class?".format(
                name, wrap_val(source_val), field.__class__.__name__
            )
        )
    return value


def deserialize_structure_reference(
        cls, the_dict: dict, *, keep_undefined, mapper, camel_case_convert=False
):
    field_by_name = {k: v for k, v in cls.__dict__.items() if isinstance(v, Field)}
    kwargs = {
        k: v for k, v in the_dict.items() if k not in field_by_name and keep_undefined
    }

    kwargs.update(
        construct_fields_map(
            field_by_name,
            keep_undefined,
            mapper,
            the_dict,
            camel_case_convert=camel_case_convert,
        )
    )
    cls(**kwargs)
    return kwargs


def construct_fields_map(
        field_by_name,
        keep_undefined,
        mapper,
        input_dict,
        camel_case_convert=False,
        ignore_none=False,
):
    result = {}
    errors = []
    mapper = mapper or {}
    for key, field in field_by_name.items():
        mapped_key = mapper.get(key, key)
        process = False
        processed_input = None
        if key in mapper:
            processed_input = get_processed_input(key, mapper, input_dict)
            if processed_input is not None:
                process = True
        elif key in input_dict and key not in mapper:
            processed_input = input_dict[key]
            process = True

        if process:
            sub_mapper = mapper.get(
                f"{mapped_key}._mapper", mapper.get(f"{key}._mapper")
            )
            if Structure.failing_fast():
                result[key] = deserialize_single_field(
                    field,
                    processed_input,
                    key,
                    mapper=sub_mapper,
                    keep_undefined=keep_undefined,
                    camel_case_convert=camel_case_convert,
                    ignore_none=ignore_none,
                )
            else:
                try:
                    result[key] = deserialize_single_field(
                        field,
                        processed_input,
                        key,
                        mapper=sub_mapper,
                        keep_undefined=keep_undefined,
                        camel_case_convert=camel_case_convert,
                        ignore_none=ignore_none,
                    )
                except (TypeError, ValueError) as ex:
                    errors.append(ex)
    if errors:
        messages = json.dumps([str(e) for e in errors])
        raise errors[0].__class__(messages) from errors[0]

    return result


def deserialize_structure_internal(
        cls,
        the_dict,
        name=None,
        *,
        mapper=None,
        keep_undefined=True,
        camel_case_convert=False,
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

    if issubclass(cls, Versioned) and isinstance(the_dict, dict) and getattr(cls, VERSION_MAPPING):
        versions_mapping = getattr(cls, VERSION_MAPPING)
        input_dict = convert_dict(the_dict, versions_mapping)
    else:
        input_dict = the_dict
    mapper = aggregate_deserialization_mappers(cls, mapper, camel_case_convert)
    if keep_undefined:
        for m in cls.get_aggregated_deserialization_mapper():
            if isinstance(m, mappers) or isinstance(mapper, mappers):
                keep_undefined = False
        if (camel_case_convert or isinstance(mapper, mappers)) and not getattr(
                cls, ADDITIONAL_PROPERTIES, False
        ):
            keep_undefined = False

    ignore_none = getattr(cls, IGNORE_NONE_VALUES, False)
    if not isinstance(mapper, (collections.Mapping,)):
        raise TypeError("Mapper must be a mapping")
    field_by_name = _get_all_fields_by_name(cls)

    if not isinstance(input_dict, dict):
        props = cls.__dict__
        fields = list(field_by_name.keys())
        required = props.get(REQUIRED_FIELDS, fields)
        additional_props = props.get(ADDITIONAL_PROPERTIES, True)
        if len(fields) == 1 and required == fields and additional_props is False:
            field_name = fields[0]
            return cls(
                deserialize_single_field(
                    getattr(cls, field_name, None),
                    input_dict,
                    field_name,
                    ignore_none=ignore_none,
                )
            )
        raise TypeError(
            "{}: Expected a dictionary; Got {}".format(name, wrap_val(input_dict))
        )

    kwargs = {
        k: v for k, v in input_dict.items() if k not in field_by_name and keep_undefined
    }

    kwargs.update(
        construct_fields_map(
            field_by_name,
            keep_undefined,
            mapper,
            input_dict,
            camel_case_convert=camel_case_convert,
            ignore_none=ignore_none,
        )
    )

    return cls(**kwargs)


def deserialize_structure(
        cls, the_dict, *, mapper=None, keep_undefined=True, camel_case_convert=False
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
        cls,
        the_dict,
        mapper=mapper,
        keep_undefined=keep_undefined,
        camel_case_convert=camel_case_convert,
    )


def _deep_get(dictionary, deep_key):
    keys = deep_key.split(".")
    return reduce(lambda d, key: d.get(key) if d else None, keys, dictionary)


def get_processed_input(key, mapper, the_dict):
    def _try_deep_get(k):
        v = _deep_get(the_dict, k)
        return v if v is not None else k

    key_mapper = mapper[key]
    if isinstance(key_mapper, (FunctionCall,)):
        args = (
            [_try_deep_get(k) for k in key_mapper.args]
            if key_mapper.args
            else [the_dict.get(key)]
        )
        processed_input = key_mapper.func(*args)
    elif isinstance(key_mapper, (str,)):
        val = _deep_get(the_dict, key_mapper)
        processed_input = val if val is not None else the_dict.get(key)
    else:
        raise TypeError(
            "mapper value must be a key in the input or a FunctionCal. Got {}".format(
                wrap_val(key_mapper)
            )
        )
    return processed_input


# pylint: disable=too-many-return-statements
def serialize_multifield_wrapper(fields, name, val, mapper, camel_case_convert):
    for field in fields:
        try:
            if getattr(field, "_validate", None):
                field._validate(val)
            if isinstance(field, TypedField) and not isinstance(val, field._ty):
                raise TypeError
            return serialize_field(field, val, camel_case_convert)
        except:
            pass
    else:
        raise ValueError(f"{name}: cannot serialize value: {val}")


def serialize_val(field_definition, name, val, mapper=None, camel_case_convert=False):
    if isinstance(field_definition, SerializableField) and isinstance(
            field_definition, Field
    ):
        return field_definition.serialize(val)
    if isinstance(field_definition, MultiFieldWrapper):
        return serialize_multifield_wrapper(field_definition.get_fields(), name, val, mapper, camel_case_convert)
    if isinstance(field_definition, (Number, Boolean, String)) or val is None:
        return val
    if isinstance(field_definition, Anything) and (isinstance(val, (int, float, str, bool)) or val is None):
        return val
    if isinstance(val, enum.Enum):
        return val.name
    if isinstance(field_definition, Enum) and isinstance(val, (int, float, str, bool)):
        return val
    if isinstance(field_definition, SizedCollection):
        if isinstance(field_definition, Map):
            if (
                    isinstance(field_definition.items, list)
                    and len(field_definition.items) == 2
            ):
                key_type, value_type = field_definition.items
                return {
                    serialize_val(
                        key_type, name, k, camel_case_convert=camel_case_convert
                    ): serialize_val(
                        value_type, name, v, camel_case_convert=camel_case_convert
                    )
                    for (k, v) in val.items()
                }
            else:
                return {
                    serialize_val(
                        Anything, name, k, camel_case_convert=camel_case_convert
                    ): serialize_val(
                        Anything, name, v, camel_case_convert=camel_case_convert
                    )
                    for (k, v) in val.items()
                }

        items = getattr(field_definition, "items", None)
        if isinstance(items, list):
            return [
                serialize_val(
                    items[ind],
                    name,
                    v,
                    mapper=mapper,
                    camel_case_convert=camel_case_convert,
                )
                for ind, v in enumerate(val)
            ]
        elif isinstance(items, Field):
            return [
                serialize_val(
                    items,
                    name,
                    i,
                    mapper=mapper,
                    camel_case_convert=camel_case_convert,
                )
                for i in val
            ]
        else:
            return [
                serialize_val(
                    None, name, i, mapper=mapper, camel_case_convert=camel_case_convert
                )
                for i in val
            ]
    if isinstance(val, (list, set, tuple)):
        return [
            serialize_val(None, name, i, camel_case_convert=camel_case_convert)
            for i in val
        ]
    if isinstance(field_definition, Anything) and isinstance(val, Structure):
        return serialize(val, mapper=mapper, camel_case_convert=camel_case_convert)
    if isinstance(val, Structure) or isinstance(field_definition, Field):
        return serialize_internal(
            val, mapper=mapper, camel_case_convert=camel_case_convert
        )

    # nothing worked. Not a typedpy field. Last ditch effort.
    try:
        return json.loads(json.dumps(val))
    except Exception as ex:
        raise ValueError(f"{name}: cannot serialize value: {ex}") from ex


def serialize_field(field_definition: Field, value, camel_case_convert=False):
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
    return serialize_val(
        field_definition,
        field_definition._name,
        value,
        camel_case_convert=camel_case_convert,
    )


def _get_mapped_value(mapper, key, items):
    if key in mapper:
        key_mapper = mapper[key]
        if isinstance(key_mapper, (FunctionCall,)):
            args = (
                [_deep_get(items, k) for k in key_mapper.args]
                if key_mapper.args
                else [items.get(key)]
            )
            return key_mapper.func(*args)
        elif not isinstance(key_mapper, (FunctionCall, str)):
            raise TypeError("mapper must have a FunctionCall or a string")

    return None


def _convert_to_camel_case_if_required(key, camel_case_convert):
    if camel_case_convert:
        words = key.split("_")
        return words[0] + "".join(w.title() for w in words[1:])
    else:
        return key


def _convert_to_snake_case_if_required(key, camel_case_convert):
    if camel_case_convert:
        return "".join(
            ["_" + char.lower() if char.isupper() else char for char in key]
        ).lstrip("_")
    else:
        return key


def serialize_internal(structure, mapper=None, compact=False, camel_case_convert=False):
    cls = structure.__class__
    field_by_name = _get_all_fields_by_name(cls)
    if isinstance(structure, (Structure, ClassReference)):
        mapper = aggregate_serialization_mappers(
            structure.__class__, mapper, camel_case_convert
        )
    mapper = {} if mapper is None else mapper
    if not isinstance(mapper, (Mapping,)):
        raise TypeError("Mapper must be a mapping")
    if isinstance(structure, getattr(Generator, "_ty", None)):
        raise TypeError("Generator cannot be serialized")
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
            field_by_name.get(key, None),
            key,
            getattr(structure, key),
            camel_case_convert=camel_case_convert,
        )
    else:
        mapper = mapper or {}
        result = {}
        items_map = dict(items)
        for key, val in items:
            if val is None:
                continue
            mapped_key = (
                mapper[key]
                if key in mapper and isinstance(mapper[key], (str,))
                else _convert_to_camel_case_if_required(key, camel_case_convert)
            )
            mapped_value = _get_mapped_value(mapper, key, items_map)
            the_field_definition = (
                Anything if mapped_value else field_by_name.get(key, None)
            )
            sub_mapper = mapper.get(f"{key}._mapper", {})
            result[mapped_key] = serialize_val(
                the_field_definition,
                key,
                mapped_value or val,
                mapper=sub_mapper,
                camel_case_convert=camel_case_convert,
            )
    return result


def serialize(value, *, mapper: Dict = None, compact=False, camel_case_convert=False):
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
             the args are a list of attributes that are arguments to the function. if args is empty it
             function transform the current attribute.
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
    if not isinstance(value, (Structure, StructureReference)):
        if value is None or isinstance(value, (int, str, bool, float)):
            return value
        if isinstance(value, (_ListStruct, _DictStruct)):
            field_definition = value._field_definition
            return serialize_val(
                field_definition,
                field_definition._name,
                value,
                camel_case_convert=camel_case_convert,
            )
        if isinstance(value, (enum.Enum,)):
            return value.name
        raise TypeError(
            "serialize: Not a Structure or Field that with an obvious serialization. Got: {}."
            " Maybe try serialize_field() instead?".format(value)
        )
    return serialize_internal(
        value, mapper=mapper, compact=compact, camel_case_convert=camel_case_convert
    )
