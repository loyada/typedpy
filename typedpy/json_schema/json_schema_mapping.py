import enum
import logging
from collections import OrderedDict
from typing import Union

from typedpy.commons import Constant, default_factories, first_in, wrap_val
from typedpy.fields import (
    FunctionCall,
    Map,
    Negative,
    NonNegative,
    NonPositive,
    Positive,
    StructureReference,
    Integer,
    Number,
    Float,
    Array,
    String,
    Boolean,
    AllOf,
    OneOf,
    AnyOf,
    NotField,
    Tuple,
    Set,
    Enum,
)

from typedpy.extfields import DateString
from typedpy.serialization.mappers import (
    DoNotSerialize,
    aggregate_serialization_mappers,
)
from typedpy.structures import (
    ADDITIONAL_PROPERTIES,
    NoneField,
    Structure,
    TypedPyDefaults,
    ClassReference,
    Field,
)

SCHEMA_PATTERN_PROPERTIES = "patternProperties"
SCHEMA_ADDITIONAL_PROPERTIES = "additionalProperties"
SCHEMA_PROPETIES = "properties"
SCHEMA_PROPERTY_NAMES = "propertyNames"


def get_mapper(field_cls):
    field_type_to_mapper = {
        StructureReference: StructureReferenceMapper,
        Integer: IntegerMapper,
        Number: NumberMapper,
        Float: NumberMapper,
        Array: ArrayMapper,
        Boolean: BooleanMapper,
        Enum: EnumMapper,
        String: StringMapper,
        DateString: DateStringMapper,
        AllOf: AllOfMapper,
        AnyOf: AnyOfMapper,
        OneOf: OneOfMapper,
        NotField: NotFieldMapper,
        Tuple: ArrayMapper,
        Set: ArrayMapper,
        Map: MapMapper,
    }
    for cls in field_cls.__mro__:
        if issubclass(cls, Field) and cls in field_type_to_mapper:
            return field_type_to_mapper[cls]
    raise NotImplementedError(f"schema mapping is not implemented for {field_cls}")


def _map_class_reference(reference, definitions_schema):
    definition, _ = structure_to_schema(getattr(reference, "_ty"), definitions_schema)
    name = getattr(reference, "_ty").__name__
    definitions_schema[name] = definition
    return {"$ref": f"#/definitions/{name}"}


def _const_to_schema(field: Constant):
    val = field()
    return {"enum": [val.name if isinstance(val, enum.Enum) else val]}


def convert_to_schema(field, definitions_schema, serialization_mapper: dict = None):
    """
    In case field is None, should return None.
    Should deal with a list of fields, as well as a single one
    """
    if field is None:
        return None
    if isinstance(field, ClassReference):
        return _map_class_reference(field, definitions_schema)
    if isinstance(field, list):
        return [
            convert_to_schema(
                f, definitions_schema, serialization_mapper=serialization_mapper
            )
            for f in field
        ]
    if isinstance(field, Constant):
        return _const_to_schema(field)
    custom = field.to_json_schema()
    if custom:
        return custom
    mapper = get_mapper(field.__class__)(field)
    return mapper.to_schema(
        definitions_schema, serialization_mapper=serialization_mapper
    )


def _validated_mapped_value(mapper, key):
    if key in mapper:
        key_mapper = mapper[key]
        if isinstance(key_mapper, (FunctionCall,)):
            logging.error(
                f"{key} is mapped to a function  in serialization mapper- "
                "This is unsupported by code-to-schema conversion. "
                "You will need to manually fix it."
            )
        elif key_mapper is DoNotSerialize or isinstance(key_mapper, Constant):
            return key_mapper
        elif not isinstance(key_mapper, (FunctionCall, str)):
            raise TypeError("mapper must have a FunctionCall or a string")

    return None


def structure_to_schema(structure, definitions_schema, serialization_mapper=None):
    """
    Generate JSON schema from :class:`Structure`
    `See working examples in tests. <https://github.com/loyada/typedpy/tree/master/tests/schema_mapping>`_

    Arguments:
        structure( subclass of :class:`Structure` ):
            the class
        definitions_schema(dict):
            the json schema for all the definitions (typically under "#/definitions" in the schema.
            If it is the first call, just use and empty dict.

    Returns:
        A tuple of 2. The fist is the schema of structure, the second is the schema
        for the referenced definitions.
        the The schema that the code maps to. It also updates

    """
    # json schema draft4 does not support inheritance, so we don't need to worry about that
    if not issubclass(structure, Structure):
        raise TypeError("Expected a Structure subclass")
    field_by_name = structure.get_all_fields_by_name()
    required = getattr(structure, "_required", list(field_by_name.keys()))

    additional_props = getattr(
        structure, ADDITIONAL_PROPERTIES, TypedPyDefaults.additional_properties_default
    )
    mapper = aggregate_serialization_mappers(structure, serialization_mapper) or {}
    if getattr(structure, "_additional_serialization") != getattr(
        Structure, "_additional_serialization"
    ):
        logging.warning(
            "mapping to schema does not support _additional_serialization method. You"
            " will have to edit it manually."
        )
    if (
        len(field_by_name) == 1
        and set(required) == set(field_by_name.keys())
        and additional_props is False
    ):
        _, value = first_in(field_by_name.items())
        return (
            convert_to_schema(value, definitions_schema),
            definitions_schema,
        )
    else:
        fields_schema = OrderedDict([("type", "object")])
        fields_schema["properties"] = {}
        properties = fields_schema["properties"]
        _generate_schema_for_fields_internal(
            definitions_schema, field_by_name, mapper, properties, required
        )
        fields_schema.update(
            OrderedDict(
                [
                    ("required", sorted(required)),
                    ("additionalProperties", additional_props),
                ]
            )
        )

    return fields_schema, definitions_schema


def _generate_schema_for_fields_internal(
    definitions_schema, field_by_name, mapper, properties, required
):
    for key, field in field_by_name.items():
        mapped_key = (
            mapper[key] if key in mapper and isinstance(mapper[key], (str,)) else key
        )
        mapped_value = _validated_mapped_value(mapper, key)
        if mapped_value is DoNotSerialize or isinstance(mapped_value, Constant):
            if mapped_key in required:
                required.pop(required.index(mapped_key))
        else:
            if key in required:
                required[required.index(key)] = mapped_key
            sub_mapper = mapper.get(f"{key}._mapper", {})
            sub_schema = convert_to_schema(
                field, definitions_schema, serialization_mapper=sub_mapper
            )
            default_raw = getattr(field, "_default", None)
            if default_raw is not None:
                default_val = default_raw() if callable(default_raw) else default_raw
                if isinstance(default_val, enum.Enum):
                    default_val = default_val.name
                sub_schema["default"] = default_val
                if mapped_key not in required:
                    required.append(mapped_key)
            properties[mapped_key] = sub_schema


type_name_to_field = {
    "object": StructureReference,
    "integer": Integer,
    "number": Number,
    "array": Array,
    "string": String,
    "boolean": Boolean,
}
multivals = {"allOf": AllOf, "anyOf": AnyOf, "oneOf": OneOf, "not": NotField}


@default_factories
def convert_to_field_code(schema, definitions, additional_fields=list):
    """
    In case schema is None, should return None.
    Should deal with a schema that is a dict, as well as one that is a list
    """

    if schema is None:
        return None
    if isinstance(schema, list):
        fields = [convert_to_field_code(s, definitions) for s in schema]
        return f"[{', '.join(fields)}]"
    if "$ref" in schema:
        def_name = schema["$ref"][len("#/definitions/") :]
        return def_name

    return _convert_field_to_schema_code_internal(
        additional_fields, definitions, schema
    )


def _convert_field_to_schema_code_internal(additional_fields, definitions, schema):
    if any(multival in schema for multival in multivals):
        for k, the_class in multivals.items():
            if k in schema:
                cls = the_class
        mapper = MultiFieldMapper

    elif "enum" in schema:
        cls = Enum
        mapper = get_mapper(cls)
    else:
        object_type = schema.get("type", "object")
        if object_type == "object":
            if SCHEMA_PROPETIES in schema:
                cls = StructureReference
            else:
                cls = Map
        else:
            for c in additional_fields:
                custom_mapping = c.from_json_schema(schema)
                if custom_mapping:
                    return custom_mapping
            cls = type_name_to_field[schema.get("type", "object")]
        mapper = get_mapper(cls)
    params_list = mapper.get_paramlist_from_schema(schema, definitions)
    _handle_schema_default_to_code(params_list, schema)
    params_as_string = ", ".join([f"{name}={val}" for (name, val) in params_list])
    return f"{cls.__name__}({params_as_string})"


def _handle_schema_default_to_code(params_list, schema):
    if "default" in schema:
        default_val = schema["default"]
        if isinstance(default_val, (list, dict)):
            default_val = f"lambda: {default_val}"
        else:
            default_val = wrap_val(default_val)
        params_list.append(("default", default_val))


@default_factories
def schema_to_struct_code(
    struct_name, schema, definitions_schema, additional_fields=list
):
    """
    Generate code for the main class that maps to the given JSON schema.
    The main struct_name can include references to structures defined in
    definitions_schema, under "#/definitions/".

    Arguments:
        struct_name(str):
            the name of the main :class:`Structure` to be created
        schema(dict):
            the json schema of the main Structure that need to be defined
        definitions_schema(dict):
            schema for definitions of objects that can be referred to in the main schema. If non exist,
            just use an empty dict.
        additional_fields(list):
            additional Types of Fields with custom schema mapping that can appear in the schema. These
            have to implement the class method from_json_schema(), which should return a string of the code
            the Schema is mapping to.
    Returns:
        A string with the code of the class. This can either be executed directly,
        using exec(), or written to a file.
        The "description" property, if exists, is mapped to the docstring of the class.
        If you write to a file, the higher level :func:`write_code_from_schema` is preferable.
        Note: In case schema is None, should return None.
        Deals with a schema that is a dict, as well as one that is a list
    """
    body = [f"class {struct_name}(Structure):"]
    body += (
        [f'    """\n    {schema.get("description")}\n    """\n']
        if "description" in schema
        else []
    )
    body += (
        ["    _additional_properties = False"]
        if not schema.get("additionalProperties", True)
        else []
    )
    required = (
        schema.get("required", None)
        if schema.get("type", "object") == "object"
        else ["wrapped"]
    )
    the_type = schema.get("type", "object" if "properties" in schema else None)

    if the_type == "object":
        properties = schema.get("properties", {})
        for name, sch in properties.items():
            if "default" in sch and name in required:
                required.remove(name)
            body += [
                f"    {name}: {convert_to_field_code(sch, definitions_schema, additional_fields=additional_fields)}"
            ]
    else:
        body += [
            f"    wrapped = {convert_to_field_code(schema, definitions_schema, additional_fields=additional_fields)}"
        ]

    body += ["", f"    _required = {required}"] if required is not None else []

    return "\n".join(body)


@default_factories
def schema_definitions_to_code(schema, additional_fields=list):
    """
    Generate code for the classes in the definitions that maps to the given JSON schema.
    `See working example in test_schema_to_code.py.
      <https://github.com/loyada/typedpy/tree/master/tests/test_schema_to_code.py>`_

    Arguments:
        schema(dict):
            the json schema of the various Structures that need to be defined
    Returns:
        A string with the code. This can either be executed directly, using exec(), or written to a file.
        If you write to a file, the higher level :func:`write_code_from_schema` is preferable.
    """
    code = []
    for name, sch in schema.items():
        code.append(
            schema_to_struct_code(
                name, sch, schema, additional_fields=additional_fields
            )
        )
    return "\n\n\n".join(code)


@default_factories
def write_code_from_schema(
    schema, definitions_schema, filename, class_name, additional_fields=list
):
    """
    Generate code from schema and write it to a file.

    Example:

    .. code-block:: python

        write_code_from_schema(
            schema,
            definitions,
            "generated_sample.py",
            "Poo",
             additional_fields=[CustomField1, CustomField2]
        )


    Arguments:
        schema(dict):
            the json schema for the main structure
        definitions_schema(dict):
            the json schema for all the definitions (typically under "#/definitions" in the schema.
            These can be referred to from the main schema
        filename(str):
            the file name for the output. Typically should be end with ".py".
        class_name(str):
            the main Structure name
        additional_fields(list[Type[Field]]):
            additional field classes with custom mapping
    """
    supporting_classes = schema_definitions_to_code(
        definitions_schema, additional_fields=additional_fields
    )
    structure_code = schema_to_struct_code(
        class_name, schema, definitions_schema, additional_fields=additional_fields
    )
    with open(filename, "w", encoding="utf-8") as fout:
        fout.write("from typedpy import *\n\n\n")
        if definitions_schema:
            fout.write(supporting_classes)
            fout.write("\n\n# ********************\n\n\n")
        fout.write(structure_code)
        fout.write("\n")


class Mapper:
    def __init__(self, value):
        self.value = value


class StructureReferenceMapper(Mapper):
    @staticmethod
    def get_paramlist_from_schema(schema, definitions):
        body = []
        body += (
            [(ADDITIONAL_PROPERTIES, False)]
            if not schema.get(SCHEMA_ADDITIONAL_PROPERTIES, True)
            else []
        )
        required = schema.get("required", None)
        body += [("_required", required)] if required is not None else []
        properties = schema.get("properties", {})

        body += [
            (k, convert_to_field_code(v, definitions)) for (k, v) in properties.items()
        ]
        return body

    def to_schema(self, definitions, serialization_mapper):
        schema, _ = structure_to_schema(
            getattr(self.value, "_newclass"), definitions, serialization_mapper
        )
        schema["type"] = "object"
        return schema


class NumberMapper(Mapper):
    @staticmethod
    def get_paramlist_from_schema(schema, definitions):
        params = {
            "multiplesOf": schema.get("multiplesOf", None),
            "minimum": schema.get("minimum", None),
            "maximum": schema.get("maximum", None),
            "exclusiveMaximum": schema.get("exclusiveMaximum", None),
        }
        return list((k, v) for k, v in params.items() if v is not None)

    def to_schema(self, definitions, serialization_mapper):
        def get_min(value):
            if value.minimum is not None:
                return value.minimum
            if isinstance(value, NonNegative):
                return 0
            if isinstance(value, Positive):
                return 1 if isinstance(value, Integer) else 0.000001
            return None

        def get_max(value):
            if value.maximum is not None:
                return value.maximum
            if isinstance(value, NonPositive):
                return 0
            if isinstance(value, Negative):
                return -1 if isinstance(value, Integer) else -0.000001
            return None

        value = self.value
        params = {
            "type": "number",
            "multiplesOf": value.multiplesOf,
            "minimum": get_min(value),
            "maximum": get_max(value),
            "exclusiveMaximum": value.exclusiveMaximum,
        }
        return {k: v for k, v in params.items() if v is not None}


class MapMapper(Mapper):
    @staticmethod
    def get_paramlist_from_schema(schema, definitions):
        additional_properties = schema.get(SCHEMA_ADDITIONAL_PROPERTIES, None)
        pattern_properties = schema.get(SCHEMA_PATTERN_PROPERTIES, None)
        property_names = schema.get(SCHEMA_PATTERN_PROPERTIES, {})
        if pattern_properties and (
            len(pattern_properties) > 1 or additional_properties or property_names
        ):
            raise NotImplementedError("Conversion for this map is unsupported")
        if not any([additional_properties, property_names, pattern_properties]):
            return []

        key_type = (
            convert_to_field_code({**property_names, "type": "string"}, globals())
            if property_names
            else "String()"
        )
        adjusted_key_type = (
            f"String(pattern='{list(pattern_properties.keys())[0]}')"
            if pattern_properties
            else key_type
        )
        value_type = (
            convert_to_field_code(additional_properties, definitions)
            if additional_properties
            else (
                convert_to_schema(pattern_properties, definitions)
                if additional_properties
                else "Anything"
            )
        )

        items = f"[{adjusted_key_type}, {value_type}]"
        params = {
            "items": items,
            "maxItems": schema.get("maxItems", None),
            "minItems": schema.get("minItems", None),
        }
        return list((k, v) for k, v in params.items() if v is not None)

    def to_schema(self, definitions, serialization_mapper):
        value = self.value
        params = {
            "type": "object",
        }
        if value.items:
            keys, values = value.items
            if not isinstance(keys, String):
                raise TypeError("JSON supports only Strings as keys")

            suffix = ""
            if keys.maxLength or keys.minLength:
                suffix = f"{{{keys.minLength or ''}, {keys.maxLength or ''}}}"
            pattern_props = f"{keys.pattern or ''}{suffix}" or None
            values_schema = convert_to_schema(
                values, definitions, serialization_mapper=serialization_mapper
            )
            if pattern_props:
                params[SCHEMA_PATTERN_PROPERTIES] = values_schema
            elif values_schema:
                params[SCHEMA_ADDITIONAL_PROPERTIES] = values_schema
        params["maxItems"] = value.maxItems
        params["minItems"] = value.minItems
        return {k: v for k, v in params.items() if v is not None}


class IntegerMapper(NumberMapper):
    def to_schema(self, definitions, serialization_mapper):
        params = super().to_schema(definitions, serialization_mapper)
        params.update({"type": "integer"})
        return params


class BooleanMapper(Mapper):
    @staticmethod
    def get_paramlist_from_schema(schema, definitions):
        return []

    def to_schema(self, definitions, serialization_mapper):
        params = {
            "type": "boolean",
        }
        return params


class StringMapper(Mapper):
    @staticmethod
    def get_paramlist_from_schema(schema, definitions):
        params = {
            "minLength": schema.get("minLength", None),
            "maxLength": schema.get("maxLength", None),
            "pattern": wrap_val(schema.get("pattern", None)),
        }
        return list((k, v) for k, v in params.items() if v is not None)

    def to_schema(self, definitions, serialization_mapper):
        value = self.value
        params = {
            "type": "string",
            "minLength": value.minLength,
            "maxLength": value.maxLength,
            "pattern": value.pattern,
        }
        return {k: v for k, v in params.items() if v is not None}


class DateStringMapper(Mapper):
    def to_schema(self, definitions, serialization_mapper):
        params = {
            "type": "string",
            "pattern": r"^([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))$",
        }
        return {k: v for k, v in params.items() if v is not None}


class ArrayMapper(Mapper):
    @staticmethod
    def get_paramlist_from_schema(schema, definitions):
        items = schema.get("items", None)
        params = {
            "uniqueItems": schema.get("uniqueItems", None),
            "additionalItems": schema.get("additionalItems", None),
            "items": convert_to_field_code(items, definitions),
        }
        return list((k, v) for k, v in params.items() if v is not None)

    def to_schema(self, definitions, serialization_mapper):
        value = self.value
        if isinstance(value, Tuple):
            params = {
                "type": "array",
                "uniqueItems": value.uniqueItems,
                "additionalItems": False,
                "items": convert_to_schema(
                    value.items, definitions, serialization_mapper
                ),
            }
        elif isinstance(value, Set):
            params = {
                "type": "array",
                "uniqueItems": True,
                "maxItems": value.maxItems,
                "minItems": value.minItems,
                "items": convert_to_schema(
                    value.items, definitions, serialization_mapper
                ),
            }
        else:
            params = {
                "type": "array",
                "uniqueItems": value.uniqueItems,
                "additionalItems": value.additionalItems,
                "maxItems": value.maxItems,
                "minItems": value.minItems,
                "items": convert_to_schema(
                    value.items, definitions, serialization_mapper
                ),
            }
        return {k: v for k, v in params.items() if v is not None}


class EnumMapper(Mapper):
    @staticmethod
    def get_paramlist_from_schema(schema, definitions):
        params = {
            "values": schema.get("enum", None),
        }
        return list(params.items())

    def to_schema(self, definitions, serialization_mapper):
        def adjust(val) -> Union[str, int, float]:
            if isinstance(val, enum.Enum):
                return (
                    val.value
                    if getattr(self.value, "serialization_by_value", False)
                    else val.name
                )
            if not isinstance(val, (int, str, float)):
                raise TypeError("enum must be an enum, str, or number")
            return val

        values = [adjust(v) for v in self.value.values]
        params = {"enum": values}
        return {k: v for k, v in params.items() if v is not None}


class MultiFieldMapper:
    @staticmethod
    def get_paramlist_from_schema(schema, definitions):
        items = list(schema.values())[0]
        params = {"fields": convert_to_field_code(items, definitions)}
        return list(params.items())


class AllOfMapper(Mapper):
    def to_schema(self, definitions, serialization_mapper):
        return {
            "allOf": convert_to_schema(
                self.value._fields, definitions, serialization_mapper
            )
        }


class OneOfMapper(Mapper):
    def to_schema(self, definitions, serialization_mapper):
        return {
            "oneOf": convert_to_schema(
                self.value._fields, definitions, serialization_mapper
            )
        }


class AnyOfMapper(Mapper):
    def to_schema(self, definitions, serialization_mapper):
        if (
            len(self.value._fields) == 2
            and self.value._fields[1].__class__ == NoneField
        ):
            return convert_to_schema(
                self.value._fields[0], definitions, serialization_mapper
            )
        return {
            "anyOf": convert_to_schema(
                self.value._fields, definitions, serialization_mapper
            )
        }


class NotFieldMapper(Mapper):
    def to_schema(self, definitions, serialization_mapper):
        return {
            "not": convert_to_schema(
                self.value._fields, definitions, serialization_mapper
            )
        }
