from collections import OrderedDict

from typedpy.fields import (
    StructureReference,
    Integer,
    Number,
    Float,
    Array,
    Enum,
    String,
    ClassReference,
    Field,
    Boolean,
    AllOf,
    OneOf,
    AnyOf,
    NotField,
    Tuple,
    Set,
)

from typedpy.extfields import DateString
from typedpy.structures import ADDITIONAL_PROPERTIES


def as_str(val):
    return "'{}'".format(val) if isinstance(val, str) else val


def get_mapper(field_cls):
    field_type_to_mapper = {
        StructureReference: StructureReferenceMapper,
        Integer: IntegerMapper,
        Number: NumberMapper,
        Float: FloatMapper,
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
    }
    for cls in field_cls.__mro__:
        if issubclass(cls, Field) and cls in field_type_to_mapper:
            return field_type_to_mapper[cls]
    raise NotImplementedError(
        "schema mapping is not implemented for {}".format(field_cls)
    )


def _map_class_reference(reference, definitions_schema):
    definition, _ = structure_to_schema(getattr(reference, "_ty"), definitions_schema)
    name = getattr(reference, "_ty").__name__
    definitions_schema[name] = definition
    return {"$ref": "#/definitions/{}".format(name)}


def convert_to_schema(field, definitions_schema):
    """
    In case field is None, should return None.
    Should deal with a list of fields, as well as a single one
    """
    if field is None:
        return None
    if isinstance(field, ClassReference):
        return _map_class_reference(field, definitions_schema)
    if isinstance(field, list):
        return [convert_to_schema(f, definitions_schema) for f in field]
    mapper = get_mapper(field.__class__)(field)
    return mapper.to_schema(definitions_schema)


def structure_to_schema(structure, definitions_schema):
    """
    Generate JSON schema from :class:`Structure`
    `See working examples in test. <https://github.com/loyada/typedpy/tree/master/tests/test_struct_to_schema.py>`_

    Arguments:
        structure( :class:`Structure` ):
            the json schema for the main structure
        definitions_schema(dict):
            the json schema for all the definitions (typically under "#/definitions" in the schema.
            If it is the first call, just use and empty dict.

    Returns:
        A tuple of 2. The fist is the schema of structure, the second is the schema
        for the referenced definitions.
        the The schema that the code maps to. It also updates

    """
    # json schema draft4 does not support inheritance, so we don't need to worry about that
    props = structure.__dict__
    fields = [key for key, val in props.items() if isinstance(val, Field)]
    required = props.get("_required", fields)
    additional_props = props.get(ADDITIONAL_PROPERTIES, True)
    if len(fields) == 1 and required == fields and additional_props is False:
        return (
            convert_to_schema(props[fields[0]], definitions_schema),
            definitions_schema,
        )
    else:
        fields_schema = OrderedDict([("type", "object")])
        fields_schema["properties"] = OrderedDict(
            [(key, convert_to_schema(props[key], definitions_schema)) for key in fields]
        )
        fields_schema.update(
            OrderedDict(
                [
                    ("required", required),
                    ("additionalProperties", additional_props),
                ]
            )
        )
    return (fields_schema, definitions_schema)


def convert_to_field_code(schema, definitions):
    """
    In case schema is None, should return None.
    Should deal with a schema that is a dict, as well as one that is a list
    """

    if schema is None:
        return None
    if isinstance(schema, list):
        fields = [convert_to_field_code(s, definitions) for s in schema]
        return "[{}]".format(", ".join(fields))
    if "$ref" in schema:
        def_name = schema["$ref"][len("#/definitions/") :]
        return def_name

    type_name_to_field = {
        "object": StructureReference,
        "integer": Integer,
        "number": Number,
        "float": Float,
        "array": Array,
        "string": String,
        "boolean": Boolean,
    }
    multivals = {"allOf": AllOf, "anyOf": AnyOf, "oneOf": OneOf, "not": NotField}
    if any(multival in schema for multival in multivals):
        for (k, the_class) in multivals.items():
            if k in schema:
                cls = the_class
        mapper = MultiFieldMapper

    elif "enum" in schema:
        cls = Enum
        mapper = get_mapper(cls)
    else:
        cls = type_name_to_field[schema.get("type", "object")]
        mapper = get_mapper(cls)
    params_list = mapper.get_paramlist_from_schema(schema, definitions)

    params_as_string = ", ".join(
        ["{}={}".format(name, val) for (name, val) in params_list]
    )
    return "{}({})".format(cls.__name__, params_as_string)


def schema_to_struct_code(struct_name, schema, definitions_schema):
    """
    Generate code for the main class that maps to the given JSON schema.
    The main struct_name can include references to structures defined in
    definitions_schema, under "#/definitions/".
    `See working examples in test. <https://github.com/loyada/typedpy/tree/master/tests/test_schema_to_code.py>`_

    Arguments:
        struct_name(str):
            the name of the main :class:`Structure` to be created
        schema(dict):
            the json schema of the main Structure that need to be defined
        definitions_schema(dict):
            schema for definitions of objects that can be referred to in the main schema. If non exist,
            just use an empty dict.
    Returns:
        A string with the code of the class. This can either be executed directly,
        using exec(), or written to a file.
        The "description" property, if exists, is mapped to the docstring of the class.
        If you write to a file, the higher level :func:`write_code_from_schema` is preferable.
        Note: In case schema is None, should return None.
        Deals with a schema that is a dict, as well as one that is a list
    """
    body = ["class {}(Structure):".format(struct_name)]
    body += (
        ['    """\n    {}\n    """\n'.format(schema.get("description"))]
        if "description" in schema
        else []
    )
    body += (
        ["    _additionalProperties = False"]
        if not schema.get("additionalProperties", True)
        else []
    )
    required = (
        schema.get("required", None)
        if schema.get("type", "object") == "object"
        else ["wrapped"]
    )
    body += ["    _required = {}".format(required)] if required is not None else []
    the_type = schema.get("type", "object" if "properties" in schema else None)

    if the_type == "object":
        properties = schema.get("properties", {})
        for (name, sch) in properties.items():
            body += [
                "    {} = {}".format(
                    name, convert_to_field_code(sch, definitions_schema)
                )
            ]
    else:
        body += [
            "    {} = {}".format(
                "wrapped", convert_to_field_code(schema, definitions_schema)
            )
        ]

    return "\n".join(body)


def schema_definitions_to_code(schema):
    """
    Generate code for the classes in the definitions that maps to the given JSON schema.
    `See working example in test. <https://github.com/loyada/typedpy/tree/master/tests/test_schema_to_code.py>`_

    Arguments:
        schema(dict):
            the json schema of the various Structures that need to be defined
    Returns:
        A string with the code. This can either be executed directly, using exec(), or written to a file.
        If you write to a file, the higher level :func:`write_code_from_schema` is preferable.
    """
    code = []
    for (name, sch) in schema.items():
        code.append(schema_to_struct_code(name, sch, schema))
    return "\n\n".join(code)


def write_code_from_schema(schema, definitions_schema, filename, class_name):
    """
    Generate code from schema and write it to a file.
    `See working examples in test. <https://github.com/loyada/typedpy/tree/master/tests/test_schema_to_code.py>`_

    Example:

    .. code-block:: python

        write_code_from_schema(schema, definitions, "generated_sample.py", "Poo")


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
    """
    supporting_classes = schema_definitions_to_code(definitions_schema)
    structure_code = schema_to_struct_code(class_name, schema, definitions_schema)
    with open(filename, "w") as fout:
        fout.write("from typedpy import *\n\n")
        fout.write(supporting_classes)
        fout.write("\n\n# ********************\n\n")
        fout.write(structure_code)
        fout.write("\n")


class Mapper(object):
    def __init__(self, value):
        self.value = value


class StructureReferenceMapper(Mapper):
    @staticmethod
    def get_paramlist_from_schema(schema, definitions):
        body = []
        body += (
            [(ADDITIONAL_PROPERTIES, False)]
            if not schema.get("additionalProperties", True)
            else []
        )
        required = schema.get("required", None)
        body += [("_required", required)] if required is not None else []
        properties = schema.get("properties", {})

        body += [
            (k, convert_to_field_code(v, definitions)) for (k, v) in properties.items()
        ]
        return body

    def to_schema(self, definitions):
        schema, _ = structure_to_schema(getattr(self.value, "_newclass"), definitions)
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

    def to_schema(self, definitions):
        value = self.value
        params = {
            "type": "number",
            "multiplesOf": value.multiplesOf,
            "minimum": value.minimum,
            "maximum": value.maximum,
            "exclusiveMaximum": value.exclusiveMaximum,
        }
        return dict([(k, v) for k, v in params.items() if v is not None])


class IntegerMapper(NumberMapper):
    def to_schema(self, definitions):
        params = super().to_schema(definitions)
        params.update({"type": "integer"})
        return params


class FloatMapper(NumberMapper):
    def to_schema(self, definitions):
        params = super().to_schema(definitions)
        params.update({"type": "float"})
        return params


class BooleanMapper(Mapper):
    @staticmethod
    def get_paramlist_from_schema(schema, definitions):
        return []

    def to_schema(self, definitions):  # pylint: disable=R0201
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
            "pattern": as_str(schema.get("pattern", None)),
        }
        return list((k, v) for k, v in params.items() if v is not None)

    def to_schema(self, definitions):
        value = self.value
        params = {
            "type": "string",
            "minLength": value.minLength,
            "maxLength": value.maxLength,
            "pattern": value.pattern,
        }
        return dict([(k, v) for k, v in params.items() if v is not None])


class DateStringMapper(Mapper):
    def to_schema(self, definitions):
        params = {
            "type": "string",
            "pattern": r"^([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))$",
        }
        return dict([(k, v) for k, v in params.items() if v is not None])


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

    def to_schema(self, definitions):
        value = self.value
        if isinstance(value, Tuple):
            params = {
                "type": "array",
                "uniqueItems": value.uniqueItems,
                "additionalItems": False,
                "items": convert_to_schema(value.items, definitions),
            }
        elif isinstance(value, Set):
            params = {
                "type": "array",
                "uniqueItems": True,
                "maxItems": value.maxItems,
                "minItems": value.minItems,
                "items": convert_to_schema(value.items, definitions),
            }
        else:
            params = {
                "type": "array",
                "uniqueItems": value.uniqueItems,
                "additionalItems": value.additionalItems,
                "maxItems": value.maxItems,
                "minItems": value.minItems,
                "items": convert_to_schema(value.items, definitions),
            }
        return dict([(k, v) for k, v in params.items() if v is not None])


class EnumMapper(Mapper):
    @staticmethod
    def get_paramlist_from_schema(schema, definitions):
        params = {
            "values": schema.get("enum", None),
        }
        return list(params.items())

    def to_schema(self, definitions):
        params = {"enum": self.value.values}
        return dict([(k, v) for k, v in params.items() if v is not None])


class MultiFieldMapper(object):
    @staticmethod
    def get_paramlist_from_schema(schema, definitions):
        items = list(schema.values())[0]
        params = {"fields": convert_to_field_code(items, definitions)}
        return list(params.items())


class AllOfMapper(Mapper):
    def to_schema(self, definitions):
        return {"allOf": convert_to_schema(self.value._fields, definitions)}


class OneOfMapper(Mapper):
    def to_schema(self, definitions):
        return {"oneOf": convert_to_schema(self.value._fields, definitions)}


class AnyOfMapper(Mapper):
    def to_schema(self, definitions):
        return {"anyOf": convert_to_schema(self.value._fields, definitions)}


class NotFieldMapper(Mapper):
    def to_schema(self, definitions):
        return {"not": convert_to_schema(self.value._fields, definitions)}
