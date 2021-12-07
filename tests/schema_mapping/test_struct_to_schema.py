from pytest import raises

from typedpy import (
    String,
    Structure,
    structure_to_schema,
    Integer,
    Array,
    StructureReference,
    Number,
    Float,
    AllOf,
    Enum,
    AnyOf,
    OneOf,
    NotField,
    Boolean,
    Map,
    Set,
    DateString,
    EmailAddress,
    Field,
    Tuple,
)


class SimpleStruct(Structure):
    name = String(pattern="[A-Za-z]+$", maxLength=8)


class Example(Structure):
    i = Integer(maximum=10)
    s = String(maxLength=5)
    a = Array[Integer(multiplesOf=5), Number]
    foo = StructureReference(a1=Integer(), a2=Float())
    ss = SimpleStruct
    ss_array = Array[SimpleStruct]
    all = AllOf[Number, Integer]
    any = AnyOf[Number(minimum=1), Integer]
    one = OneOf[Number(minimum=1), Integer]
    no = NotField(fields=[String])
    enum = Enum(values=[1, 2, 3])
    a_set = Set[Integer]
    a_tuple = Tuple[String, Integer]


def test_class_reference_in_definitions():
    schema, definitions = structure_to_schema(Example, {})
    assert definitions == {
        "SimpleStruct": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "pattern": "[A-Za-z]+$", "maxLength": 8}
            },
            "required": ["name"],
            "additionalProperties": True,
        }
    }


def test_schema():
    schema, definitions = structure_to_schema(Example, {})
    assert set(schema["required"]) == {
        "a",
        "all",
        "any",
        "one",
        "no",
        "i",
        "foo",
        "ss",
        "ss_array",
        "s",
        "enum",
        "a_set",
        "a_tuple",
    }
    del schema["required"]
    assert set(schema["properties"]["foo"]["required"]) == {"a1", "a2"}
    del schema["properties"]["foo"]["required"]
    assert dict(schema) == {
        "type": "object",
        "properties": {
            "a": {
                "items": [{"multiplesOf": 5, "type": "integer"}, {"type": "number"}],
                "type": "array",
            },
            "all": {"allOf": [{"type": "number"}, {"type": "integer"}]},
            "any": {"anyOf": [{"type": "number", "minimum": 1}, {"type": "integer"}]},
            "one": {"oneOf": [{"type": "number", "minimum": 1}, {"type": "integer"}]},
            "no": {"not": [{"type": "string"}]},
            "i": {"maximum": 10, "type": "integer"},
            "foo": {
                "type": "object",
                "properties": {"a2": {"type": "float"}, "a1": {"type": "integer"}},
                "additionalProperties": True,
            },
            "ss": {"$ref": "#/definitions/SimpleStruct"},
            "ss_array": {
                "type": "array",
                "items": {"$ref": "#/definitions/SimpleStruct"},
            },
            "s": {"type": "string", "maxLength": 5},
            "enum": {"enum": [1, 2, 3]},
            "a_set": {
                "type": "array",
                "uniqueItems": True,
                "items": {"type": "integer"},
            },
            "a_tuple": {
                "type": "array",
                "additionalItems": False,
                "items": [{"type": "string"}, {"type": "integer"}],
            },
        },
        "additionalProperties": True,
    }


def test_array_no_items_definition():
    class Foo(Structure):
        arr = Array(minItems=2)
        _required = []
        _additionalProperties = False

    schema, definitions = structure_to_schema(Foo, {})
    assert schema == {
        "type": "object",
        "properties": {"arr": {"type": "array", "minItems": 2}},
        "required": [],
        "additionalProperties": False,
    }


def test_boolean_field():
    class Foo(Structure):
        b = Boolean

    schema, definitions = structure_to_schema(Foo, {})
    assert schema == {
        "type": "object",
        "properties": {"b": {"type": "boolean"}},
        "required": ["b"],
        "additionalProperties": True,
    }


def test_single_boolean_field_wrapper():
    class Foo(Structure):
        b = Boolean
        _required = ["b"]
        _additionalProperties = False

    schema, definitions = structure_to_schema(Foo, {})
    assert schema == {"type": "boolean"}


def test_single_array_field_wrapper():
    class Foo(Structure):
        arr = Array(minItems=2)
        _required = ["arr"]
        _additionalProperties = False

    schema, definitions = structure_to_schema(Foo, {})
    assert schema == {"type": "array", "minItems": 2}


def test_single_array_field_not_just_wrapper():
    class Foo(Structure):
        arr = Array(minItems=2)

    schema, definitions = structure_to_schema(Foo, {})
    assert schema == {
        "type": "object",
        "properties": {"arr": {"type": "array", "minItems": 2}},
        "required": ["arr"],
        "additionalProperties": True,
    }


def test_datestring_field():
    class Foo(Structure):
        a = DateString

    schema, definitions = structure_to_schema(Foo, {})
    assert schema == {
        "type": "object",
        "properties": {
            "a": {
                "type": "string",
                "pattern": "^([12]\\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\\d|3[01]))$",
            }
        },
        "required": ["a"],
        "additionalProperties": True,
    }


def test_email_field():
    class Foo(Structure):
        a = EmailAddress

    schema, definitions = structure_to_schema(Foo, {})
    assert schema == {
        "type": "object",
        "properties": {
            "a": {
                "type": "string",
                "pattern": "(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9]+$)",
            }
        },
        "required": ["a"],
        "additionalProperties": True,
    }


def test_unsupported_field():
    class AAA(Field):
        pass

    class Foo(Structure):
        a = AAA

    with raises(NotImplementedError):
        structure_to_schema(Foo, {})
