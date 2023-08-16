from pytest import raises

from typedpy import *

definitions = {
    "SimpleStruct": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "pattern": "[A-Za-z]+$", "maxLength": 8}
        },
        "required": ["name"],
        "additionalProperties": True,
    },
    "ComplexStruct": {
        "type": "object",
        "properties": {"simple": {"$ref": "#/definitions/SimpleStruct"}},
    },
}

schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "description": "This is a test of schema mapping",
    "properties": {
        "foo": {
            "type": "object",
            "properties": {
                "a2": {"type": "number"},
                "a1": {"type": "integer"},
            },
            "required": ["a2", "a1"],
            "additionalProperties": True,
        },
        "ss": {"$ref": "#/definitions/ComplexStruct"},
        "enum": {"enum": [1, 2, 3]},
        "s": {"maxLength": 5, "type": "string"},
        "i": {"type": "integer", "maximum": 10},
        "all": {"allOf": [{"type": "number"}, {"type": "integer"}]},
        "a": {
            "type": "array",
            "items": [{"type": "integer", "multiplesOf": 5}, {"type": "number"}],
        },
    },
    "required": ["foo", "ss", "enum", "s", "i", "all", "a"],
    "additionalProperties": True,
    "definitions": {
        "SimpleStruct": {
            "type": "object",
            "properties": {
                "name": {"maxLength": 8, "type": "string", "pattern": "[A-Za-z]+$"}
            },
            "required": ["name"],
            "additionalProperties": True,
        }
    },
}


def test_definitions():
    code = schema_definitions_to_code(definitions)
    exec(code, globals())
    assert SimpleStruct(name="abc").name == "abc"


def test_schema():
    definitions_code = schema_definitions_to_code(definitions)
    exec(definitions_code, globals())

    struct_code = schema_to_struct_code("Duba", schema, definitions)
    exec(struct_code, globals())
    duba = Duba(
        foo={"a1": 5, "a2": 1.5},
        ss=ComplexStruct(simple=SimpleStruct(name="abc")),
        enum=2,
        s="xyz",
        i=10,
        all=6,
        a=[10, 3],
    )
    assert duba.ss.simple.name == "abc"


def test_write_code_to_file():
    write_code_from_schema(schema, definitions, "generated_sample.py", "Poo")
    from importlib.machinery import SourceFileLoader
    import os

    cwd = os.getcwd()
    generated_sample = SourceFileLoader(
        "generated_sample", cwd + "/" + "generated_sample.py"
    ).load_module()
    # from generated_sample import Poo, ComplexStruct
    poo = generated_sample.Poo(
        foo={"a1": 5, "a2": 1.5},
        ss=generated_sample.ComplexStruct(
            simple=generated_sample.SimpleStruct(name="abc")
        ),
        enum=2,
        s="xyz",
        i=10,
        all=6,
        a=[10, 3],
    )
    assert poo.ss.simple.name == "abc"
    assert "This is a test of schema mapping" == generated_sample.Poo.__doc__.strip()
    from os import remove

    remove("generated_sample.py")


def test_array_no_items_definition():
    schema = {
        "type": "object",
        "properties": {
            "arr": {
                "type": "array",
                "uniqueItems": True,
            }
        },
        "required": [],
        "additionalProperties": False,
    }
    struct_code = schema_to_struct_code("Duba", schema, {})
    exec(struct_code, globals())

    duba = Duba(arr=[1, "sss", None])
    assert duba.arr[2] is None


def test_boolean_field():
    schema = {
        "type": "object",
        "b": {"type": "boolean"},
        "required": ["b"],
        "additionalProperties": True,
    }

    struct_code = schema_to_struct_code("Foo", schema, {})
    exec(struct_code, globals())

    foo = Foo(b=False)
    assert foo.b == False


def test_array_top_level():
    schema = {
        "type": "array",
        "items": [{"type": "integer", "multiplesOf": 5}, {"type": "number"}],
    }

    struct_code = schema_to_struct_code("Foo", schema, {})
    exec(struct_code, globals())

    foo = Foo(wrapped=[10, 4])
    assert foo.wrapped[1] == 4


def test_array_top_level_1():
    schema = {
        "type": "array",
        "items": [{"type": "integer", "multiplesOf": 5}, {"type": "number"}],
    }

    struct_code = schema_to_struct_code("Foo", schema, {})
    exec(struct_code, globals())

    foo = Foo([10, 4])
    assert foo.wrapped[1] == 4


def test_array_top_level_err():
    schema = {
        "type": "array",
        "items": [{"type": "integer", "multiplesOf": 5}, {"type": "number"}],
    }

    struct_code = schema_to_struct_code("Foo", schema, {})
    exec(struct_code, globals())
    with raises(TypeError) as excinfo:
        Foo(wrapped=123)


def test_enum_top_level():
    schema = {"enum": [1, 2, 3]}

    struct_code = schema_to_struct_code("Foo", schema, {})
    exec(struct_code, globals())

    foo = Foo(2)
    assert foo.wrapped == 2


def test_enum_top_level_err():
    schema = {"enum": [1, 2, 3]}

    struct_code = schema_to_struct_code("Foo", schema, {})
    exec(struct_code, globals())
    with raises(ValueError) as excinfo:
        Foo("abc")
