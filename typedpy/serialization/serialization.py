import collections
import enum
import json
import uuid
from functools import lru_cache
from typing import Dict
from decimal import Decimal

from typedpy.commons import (
    Constant,
    Undefined,
    deep_get,
    raise_errs_if_needed,
    wrap_val,
)
from typedpy.serialization.versioned_mapping import (
    VERSIONS_MAPPING,
    Versioned,
    convert_dict,
)
from typedpy.serialization.mappers import (
    DoNotSerialize,
    aggregate_deserialization_mappers,
    aggregate_serialization_mappers,
    get_flat_resolved_mapper,
    mappers,
)
from typedpy.structures import (
    TypedField,
    Structure,
    TypedPyDefaults,
    ADDITIONAL_PROPERTIES,
    REQUIRED_FIELDS,
    IGNORE_NONE_VALUES,
    NoneField,
    Field,
    ClassReference,
)
from typedpy.structures.consts import (
    DESERIALIZATION_MAPPER,
    ENABLE_UNDEFINED,
    SERIALIZATION_MAPPER,
)
from typedpy.fields import (
    Enum,
    FunctionCall,
    Number,
    SizedCollection,
    String,
    Float,
    Integer,
    StructureReference,
    Array,
    Map,
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
    Deque,
    Generator,
    _DictStruct,
    _ListStruct,
)
from .fast_serialization import FastSerializable, create_serializer
from ..structures.structures import (
    created_fast_serializer,
    failed_to_create_fast_serializer,
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
        raise ValueError(f"{name}: Got {value}; Expected a list, set, or tuple")

    values = []
    items = field.items
    if isinstance(items, Field):
        ignore_none = getattr(items, IGNORE_NONE_VALUES, False)
        for i, v in enumerate(value):
            item_name = f"{name}_{i}"
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
                prefix = "" if str(e).startswith(item_name) else f"{item_name}: "
                raise ValueError(f"{prefix}{str(e)}") from e
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
                raise ValueError(f"{name}_{i}: {str(e)}") from e
            values.append(res)
        values += value[len(items) :]
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
                    f"{name}: Got {wrap_val(source_val)}; Matches field {field}, but must not match it"
                )
            elif isinstance(field, OneOf) and found_previous_match:
                raise ValueError(
                    f"{name}: Got {wrap_val(source_val)}; Matches more than one match"
                )
            found_previous_match = True
        except Exception as e:
            failures += 1
            err_messages.append(
                f"({len(err_messages) + 1}) Does not match {field_option}. reason: {str(e)}"
            )
            if isinstance(field, AllOf):
                raise ValueError(
                    f"{name}: Got {wrap_val(source_val)}; Does not match {field_option}. reason: {str(e)}"
                ) from e
    if failures == len(field.get_fields()) and not isinstance(field, NotField):
        raise ValueError(
            f"{name}: Got {wrap_val(source_val)}; Does not match any field option: {'. '.join(err_messages)}"
        )
    return deserialized


def deserialize_map(map_field, source_val, name, camel_case_convert=False):
    if not isinstance(source_val, dict):
        raise TypeError(f"{name}: Got {wrap_val(source_val)}; Expected a dictionary")
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
    name="value",
    *,
    mapper=None,
    keep_undefined=True,
    camel_case_convert=False,
    ignore_none=False,
):
    """
    Deserialize a field directly, without the need to define a Structure class.
    Note the top level must be a python dict - which implies that a JSON of

    Arguments:
        field(Field):
            The field definition. For example: String, Array[Map[str, Foo]], AnyOf[Foo, Bar]
        source_val:
            the serialized value to be deserialized
        name(optional):
            name to be used for the field in case of raised exceptions
        mapper(dict): optional
            A Typedpy deserialization mapper
        keep_undefined(bool): optional
            should it create attributes for keys that don't appear in the class? default is True.

    Returns:
        a deserialized version of the data if successful, or raises an appropriate exception
    """
    if source_val is None and (ignore_none or isinstance(field, NoneField)):
        return source_val
    if isinstance(field, (Number, String, Boolean)) and not isinstance(
        field, SerializableField
    ):
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
            raise ValueError(f"{name}: Got {wrap_val(source_val)}; {str(e)}") from e
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
        raise ValueError(f"{name}: Got {wrap_val(source_val)}; Expected None")
    else:
        raise NotImplementedError(
            f"{name}: Got {wrap_val(source_val)}; Cannot deserialize value of type {field.__class__.__name__}. Are "
            "you using non-Typepy class? "
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
            cls=cls,
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
    cls,
    use_strict_mapping=False,
    camel_case_convert=False,
    ignore_none=False,
    enable_undefined=False,
):
    result = {}
    errors = []
    mapper = mapper or {}
    for key, field in field_by_name.items():
        mapped_key = mapper.get(key, key)
        if mapped_key in getattr(cls, "_constants", []):
            continue
        process = False
        processed_input = None
        if key in mapper:
            processed_input = get_processed_input(
                key,
                mapper,
                input_dict,
                enable_undefined=enable_undefined,
                use_strict_mapping=use_strict_mapping,
            )
            if processed_input is not None or getattr(cls, ENABLE_UNDEFINED, False):
                process = True
        elif key in input_dict and key not in mapper:
            processed_input = input_dict[key]
            process = True

        if process:
            sub_mapper = mapper.get(
                f"{mapped_key}._mapper", mapper.get(f"{key}._mapper")
            )
            if processed_input is not Undefined:
                if Structure.failing_fast() and processed_input:
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

    raise_errs_if_needed(cls, errors)
    return result


class _ClsSimplicity(enum.Enum):
    not_nested = 1
    nested = 2


_valid_classes_for_trusted_deserialization = (
    Integer,
    String,
    Float,
    Boolean,
    NoneField,
    Enum,
    SerializableField,
    Number,
)


def _is_mapper_simple(cls) -> bool:
    mapper = getattr(
        cls, DESERIALIZATION_MAPPER, getattr(cls, SERIALIZATION_MAPPER, {})
    )
    if not mapper:
        return True
    if mapper in [mappers.NO_MAPPER, mappers.TO_CAMELCASE, mappers.TO_LOWERCASE]:
        return True
    if not isinstance(mapper, dict):
        return False
    for k, v in mapper.items():
        if k.endswith("._mapper"):
            return False
        if not isinstance(v, str):
            return False

    return True


def _is_optional_anyof(field: AnyOf) -> bool:
    return len(field.get_fields()) == 2 and NoneField in [
        x.__class__ for x in field.get_fields()
    ]


def _extract_non_nonefield_from_optional(field: AnyOf) -> Field:
    fields = field.get_fields()
    return fields[0] if fields[1].__class__ is NoneField else fields[0]


@lru_cache(maxsize=128)
def _structure_simplicity_level(cls):
    mapper_is_valid = _is_mapper_simple(cls)
    if not mapper_is_valid:
        raise ValueError(
            f"class {cls.__name__} has a mapper that is unsupported for trusted deserialization"
        )

    simplicity = _ClsSimplicity.not_nested
    for v in cls.get_all_fields_by_name().values():
        if isinstance(v, SerializableField):
            simplicity = _ClsSimplicity.nested
        if isinstance(v, _valid_classes_for_trusted_deserialization):
            continue
        if isinstance(v, AnyOf):
            for f in v.get_fields():
                if _is_optional_anyof(v):
                    simplicity = _ClsSimplicity.nested
                    continue
                if not isinstance(f, _valid_classes_for_trusted_deserialization):
                    return False
            continue
        if isinstance(v, Array):
            if isinstance(v, SerializableField):
                simplicity = _ClsSimplicity.nested
            if isinstance(v.items, _valid_classes_for_trusted_deserialization):
                continue
            if isinstance(v.items, ClassReference) and _structure_simplicity_level(
                v.items.get_type
            ):
                simplicity = _ClsSimplicity.nested
                continue
            return False
        if isinstance(v, Set):
            if isinstance(v.items, _valid_classes_for_trusted_deserialization):
                simplicity = _ClsSimplicity.nested
                continue
            if isinstance(v.items, ClassReference) and _structure_simplicity_level(
                v.items.get_type
            ):
                simplicity = _ClsSimplicity.nested
                continue
            return False
        if isinstance(v, ClassReference) and _structure_simplicity_level(v.get_type):
            simplicity = _ClsSimplicity.nested
            continue
        return False

    return simplicity


@lru_cache(maxsize=128)
def _get_enum_mapping(cls):
    without_optionals = {
        k: getattr(v, "_enum_class")
        for k, v in cls.get_all_fields_by_name().items()
        if isinstance(v, Enum) and getattr(v, "_is_enum", False)
    }
    optionals =  {
        k: getattr(getattr(v, "_fields")[0], "_enum_class")
        for k, v in cls.get_all_fields_by_name().items()
        if isinstance(v, AnyOf) and getattr(v, "_is_optional") and isinstance(getattr(v, "_fields")[0], Enum)
    }
    return {**without_optionals, **optionals}


@lru_cache(maxsize=128)
def _get_class_deserialization_mapping_for_simple_class(cls):
    return get_flat_resolved_mapper(cls)


def _extract_mapped_key(deserialization_mapper, key):
    if key.endswith("._mapper"):
        return key[:-8]
    return deserialization_mapper[key]


def _remap_input(
    input_dict,
    cls,
    *,
    name,
    use_strict_mapping,
    simple_structure_verified,
    camel_case_convert,
    keep_undefined,
):
    corrected_input = {}
    for k, v in input_dict.items():
        field_def = cls.get_all_fields_by_name().get(k)
        if v is None:
            if getattr(cls, ENABLE_UNDEFINED, False) or not getattr(
                cls, IGNORE_NONE_VALUES, False
            ):
                corrected_input[k] = None
            continue
        if (
            isinstance(field_def, AnyOf)
            and _is_optional_anyof(field_def)
            and v is not None
        ):
            field_def = _extract_non_nonefield_from_optional(field_def)

        if isinstance(field_def, ClassReference):
            corrected_input[k] = deserialize_structure_internal(
                field_def.get_type,
                v,
                name,
                use_strict_mapping=use_strict_mapping,
                camel_case_convert=camel_case_convert,
                keep_undefined=keep_undefined,
                simple_structure_verified=simple_structure_verified,
                direct_trusted_mapping=True,
            )
        elif isinstance(field_def, Enum):
            corrected_input[k] = v
        elif isinstance(field_def, SerializableField):
            corrected_input[k] = field_def.deserialize(v)
        elif isinstance(field_def, Array):
            if isinstance(field_def.items, ClassReference):
                corrected_input[k] = [
                    deserialize_structure_internal(
                        field_def.items.get_type,
                        x,
                        name,
                        use_strict_mapping=use_strict_mapping,
                        camel_case_convert=camel_case_convert,
                        keep_undefined=keep_undefined,
                        simple_structure_verified=simple_structure_verified,
                        direct_trusted_mapping=True,
                    )
                    for x in v
                ]
            elif isinstance(field_def.items, SerializableField):
                corrected_input[k] = field_def.items.deserialize(v)
            else:
                corrected_input[k] = v

        elif isinstance(field_def, Set):
            if isinstance(
                field_def.items, (Integer, String, Float, Boolean, NoneField)
            ):
                corrected_input[k] = set(v)
            elif isinstance(field_def.items, SerializableField):
                corrected_input[k] = {field_def.items.deserialize(x) for x in v}
            elif isinstance(field_def.items, ClassReference):
                corrected_input[k] = {
                    deserialize_structure_internal(
                        field_def.items.get_type,
                        x,
                        name,
                        use_strict_mapping=use_strict_mapping,
                        camel_case_convert=camel_case_convert,
                        keep_undefined=keep_undefined,
                        simple_structure_verified=simple_structure_verified,
                        direct_trusted_mapping=True,
                    )
                    for x in v
                }
        else:
            corrected_input[k] = v
    return corrected_input


def deserialize_structure_internal(
    cls,
    the_dict,
    name=None,
    *,
    use_strict_mapping=False,
    mapper=None,
    keep_undefined=False,
    camel_case_convert=False,
    direct_trusted_mapping=False,
    simple_structure_verified=False,
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

    input_dict = the_dict
    if issubclass(cls, Versioned):
        if not isinstance(the_dict, dict) or "version" not in the_dict:
            raise TypeError("Expected a dictionary with a 'version' value")
        if getattr(cls, VERSIONS_MAPPING):
            versions_mapping = getattr(cls, VERSIONS_MAPPING)
            input_dict = convert_dict(the_dict, versions_mapping)

    if (
        direct_trusted_mapping
        and not mapper
        and (simple_structure_verified or _structure_simplicity_level(cls))
        and not camel_case_convert
    ):
        deserialization_mapper = _get_class_deserialization_mapping_for_simple_class(
            cls
        )
        if deserialization_mapper:
            input_dict = {
                deserialization_mapper.get(k, k): input_dict[k] for k in input_dict
            }

        enum_mapping = _get_enum_mapping(cls)
        if enum_mapping:
            enum_vals = {
                k: mapping[input_dict[k]]
                for k, mapping in enum_mapping.items()
                if input_dict.get(k)
            }
            updated_input = {**input_dict, **enum_vals}
        else:
            updated_input = input_dict

        simple_structure_type = (
            simple_structure_verified
            if simple_structure_verified
            else _structure_simplicity_level(cls)
        )
        remapped_input = (
            _remap_input(
                updated_input,
                cls,
                name=name,
                use_strict_mapping=use_strict_mapping,
                simple_structure_verified=simple_structure_type,
                camel_case_convert=camel_case_convert,
                keep_undefined=keep_undefined,
            )
            if simple_structure_type is _ClsSimplicity.nested
            else updated_input
        )

        return cls.from_trusted_data(remapped_input)

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
    field_by_name = cls.get_all_fields_by_name()
    props = cls.__dict__
    additional_props = props.get(
        ADDITIONAL_PROPERTIES, TypedPyDefaults.additional_properties_default
    )
    if not isinstance(input_dict, dict):
        fields = list(field_by_name.keys())
        required = props.get(REQUIRED_FIELDS, fields)

        if (
            len(fields) == 1
            and required == fields
            and additional_props is False
            and TypedPyDefaults.compact_deserialization_default
        ):
            field_name = fields[0]
            return cls(
                deserialize_single_field(
                    getattr(cls, field_name, None),
                    input_dict,
                    field_name,
                    ignore_none=ignore_none,
                )
            )
        raise TypeError(f"{name}: Expected a dictionary; Got {wrap_val(input_dict)}")

    kwargs = {
        k: v
        for k, v in input_dict.items()
        if k not in field_by_name
        and keep_undefined and
        (additional_props is True or not TypedPyDefaults.ignore_invalid_additional_properties_in_deserialization)
        and k not in getattr(cls, "_constants", [])
    }

    kwargs.update(
        construct_fields_map(
            field_by_name,
            keep_undefined,
            mapper,
            input_dict,
            cls=cls,
            use_strict_mapping=use_strict_mapping,
            camel_case_convert=camel_case_convert,
            ignore_none=ignore_none,
            enable_undefined=getattr(cls, ENABLE_UNDEFINED, False),
        )
    )

    return cls(**kwargs)


def deserialize_structure(
    cls,
    the_dict,
    *,
    use_strict_mapping=False,
    mapper=None,
    keep_undefined=True,
    camel_case_convert=False,
    direct_trusted_mapping=False,
):
    """
    Deserialize a dict to a Structure instance, Jackson style.
    `See working examples in test. <https://github.com/loyada/typedpy/tree/master/tests/test_deserialization.py>`_

    Arguments:
        cls(type):
            The target class
        the_dict(dict):
            the source dictionary
        use_strict_mapping(bool): Optional
            If True, in case a mapper maps field "x" to a key "y" in the input, will not use key "x" in the input
            event if value for "y" does not exist. Default is False.
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
        use_strict_mapping=use_strict_mapping,
        mapper=mapper,
        keep_undefined=keep_undefined,
        camel_case_convert=camel_case_convert,
        direct_trusted_mapping=direct_trusted_mapping,
    )


SENTITNEL = uuid.uuid4()


def get_processed_input(key, mapper, the_dict, *, enable_undefined, use_strict_mapping):
    def _get_arg_list(key_mapper):
        vals = [deep_get(the_dict, k, default=SENTITNEL) for k in key_mapper.args]
        return [v for v in vals if v != SENTITNEL]

    key_mapper = mapper[key]
    if isinstance(key_mapper, (FunctionCall,)):
        args = _get_arg_list(key_mapper) if key_mapper.args else [the_dict.get(key)]
        processed_input = key_mapper.func(*args) if args else None
    elif isinstance(key_mapper, (str,)):
        val = deep_get(the_dict, key_mapper, enable_undefined=enable_undefined)
        processed_input = (
            val if (val is not None or use_strict_mapping) else the_dict.get(key)
        )
    elif isinstance(key_mapper, Constant):
        processed_input = key_mapper()
    else:
        raise TypeError(
            f"mapper value must be a key in the input or a FunctionCal. Got {wrap_val(key_mapper)}"
        )
    return processed_input


# pylint: disable=too-many-return-statements
def serialize_multifield_wrapper(fields, name, val, mapper, camel_case_convert):
    for field in fields:
        try:
            if getattr(field, "_validate", None):
                field._validate(val)
            return serialize_field(field, val, camel_case_convert)
        except:  # pylint: disable=bare-except
            pass
    else:  # pylint: disable=useless-else-on-loop
        raise ValueError(f"{name}: cannot serialize value: {val}")


def serialize_val(
    field_definition, name, val, mapper=None, camel_case_convert=False, cache=None
):
    if cache is None:
        cache = {}
    if field_definition in cache:
        return cache[field_definition](val)
    if isinstance(field_definition, SerializableField):
        cache[field_definition] = field_definition.serialize
        return field_definition.serialize(val)
    if isinstance(field_definition, MultiFieldWrapper):
        return serialize_multifield_wrapper(
            field_definition.get_fields(), name, val, mapper, camel_case_convert
        )
    if isinstance(field_definition, (Number, Boolean, String)) or val is None:
        return str(val) if isinstance(val, Decimal) else val
    if isinstance(field_definition, Anything) and (
        isinstance(val, (int, float, str, bool)) or val is None
    ):
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
        resolved_mapper = (
            aggregate_serialization_mappers(
                val.__class__,
                override_mapper=None,
                camel_case_convert=camel_case_convert,
            )
            if (
                isinstance(field_definition, ClassReference)
                and isinstance(val, field_definition.get_type)
                and val.__class__ is not field_definition.get_type
            )
            else mapper
        )

        return serialize_internal(
            val, resolved_mapper=resolved_mapper, camel_case_convert=camel_case_convert
        )
    if isinstance(field_definition, Constant):
        return val.name if isinstance(val, enum.Enum) else val
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
        if type(key_mapper) is str:
            return None
        if isinstance(key_mapper, (FunctionCall,)):
            args = (
                [deep_get(items, k) for k in key_mapper.args]
                if key_mapper.args
                else [items.get(key)]
            )
            return key_mapper.func(*args)
        elif key_mapper is DoNotSerialize:
            return key_mapper
        elif isinstance(key_mapper, Constant):
            return key_mapper()
        elif not isinstance(key_mapper, (FunctionCall, str)):
            raise TypeError("mapper must have a FunctionCall or a string")

    return None


def _convert_to_camel_case_if_required(key, camel_case_convert):
    if camel_case_convert:
        words = key.split("_")
        return words[0] + "".join(w.title() for w in words[1:])
    else:
        return key


def serialize_internal(
    structure,
    mapper=None,
    resolved_mapper=None,
    compact=False,
    camel_case_convert=False,
):
    cls = structure.__class__
    if issubclass(cls, FastSerializable) and not mapper:
        if (
            "serialize" not in cls.__dict__
            or structure.__class__.serialize is FastSerializable.serialize
        ) and not getattr(cls, failed_to_create_fast_serializer, False):
            try:
                create_serializer(cls, compact=compact, mapper=resolved_mapper)
            except Exception:
                setattr(cls, failed_to_create_fast_serializer, True)
        if getattr(cls, created_fast_serializer, False):
            return structure.serialize()

    field_by_name = cls.get_all_fields_by_name() if issubclass(cls, Structure) else {}
    if isinstance(structure, (Structure, ClassReference)):
        mapper = (
            resolved_mapper
            if resolved_mapper
            else aggregate_serialization_mappers(
                structure.__class__, mapper, camel_case_convert
            )
        )
    mapper = {} if mapper is None else mapper
    if isinstance(structure, getattr(Generator, "_ty", None)):
        raise TypeError("Generator cannot be serialized")
    nones = [(k, None) for k in getattr(structure, "_none_fields", [])]

    items = (
        list(structure.items())
        if isinstance(structure, dict)
        else [
            (k, v)
            for (k, v) in structure.__dict__.items()
            if k not in ["_instantiated", "_none_fields", "_trust_supplied_values"]
        ]
    ) + nones
    props = structure.__class__.__dict__
    fields = list(field_by_name.keys())
    additional_props = props.get(
        ADDITIONAL_PROPERTIES, TypedPyDefaults.additional_properties_default
    )
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
            if val is None and not getattr(structure, ENABLE_UNDEFINED, False):
                continue
            mapped_key = (
                mapper[key]
                if key in mapper and isinstance(mapper[key], (str,))
                else _convert_to_camel_case_if_required(key, camel_case_convert)
            )
            mapped_value = _get_mapped_value(mapper, key, items_map)
            if mapped_value is not DoNotSerialize:
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
    if getattr(structure, "_additional_serialization", None):
        additional_props = structure._additional_serialization()
        if not isinstance(additional_props, dict):
            raise TypeError("_additional_serialization must return a dict")
        for key, value in additional_props.items():
            result[key] = value() if callable(value) else value
    return result


def serialize(
    value,
    *,
    mapper: Dict = None,
    compact=None,
    camel_case_convert=False,
):
    """
    Serialize an instance of :class:`Structure` to a JSON-like dict.

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
    compact = (
        TypedPyDefaults.compact_serialization_default if compact is None else compact
    )
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
            f"serialize: Not a Structure or Field that with an obvious serialization. Got: {value}."
            " Maybe try serialize_field() instead?"
        )
    return serialize_internal(
        value, mapper=mapper, compact=compact, camel_case_convert=camel_case_convert
    )


class HasTypes:
    """
    A mixin that can be added to a base-class :class:`Structure`. It adds to the serialization of
    any instance of a subclass, its type.
    Since version 2.12.1.
    """

    def _additional_serialization(self) -> dict:
        return {"type": self.__class__.__name__.lower()}
