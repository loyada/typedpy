from pytest import raises

from typedpy import String, Structure, structure_to_schema, Integer, Array, \
    StructureReference, Number, Float, AllOf, Enum, AnyOf, OneOf, NotField


class SimpleStruct(Structure):
    name = String(pattern='[A-Za-z]+$', maxLength=8)

class Example(Structure):
    i = Integer(maximum=10)
    s = String(maxLength=5)
    a = Array[Integer(multiplesOf=5), Number]
    foo = StructureReference(a1 = Integer(), a2=Float())
    ss = SimpleStruct
    all = AllOf[Number, Integer]
    any = AnyOf[Number(minimum=1), Integer]
    one = OneOf[Number(minimum=1), Integer]
    no = NotField(fields = [String])
    enum = Enum(values=[1,2,3])

def test_class_reference_in_definitions():
    schema, definitions = structure_to_schema(Example, {})
    assert definitions == {
        "SimpleStruct": {
            "type": "object",
            "name": {
                "type": "string",
                "pattern": "[A-Za-z]+$",
                "maxLength": 8
            },
            "required": [
                "name"
            ],
            "additionalProperties": True
        }
    }

def test_schema():
    schema, definitions = structure_to_schema(Example, {})
    assert set(schema['required']) == {'a', 'all', 'any','one', 'no',
                                       'i', 'foo', 'ss', 's', 'enum'}
    del schema['required']
    assert set(schema['foo']['required']) == {'a1','a2'}
    del schema['foo']['required']
    assert dict(schema) == {
            "type": "object",
            "a": {
                "items": [
                    {
                        "multiplesOf": 5,
                        "type": "integer"
                    },
                    {
                        "type": "number"
                    }
                ],
                "type": "array"
            },
            "all": {
                "allOf": [
                    {
                        "type": "number"
                    },
                    {
                        "type": "integer"
                    }
                ]
            },
            "any": {
              "anyOf": [
                    {
                        "type": "number",
                        "minimum": 1
                    },
                    {
                        "type": "integer"
                    }
                ]
            },
            "one": {
                "oneOf": [
                    {
                        "type": "number",
                        "minimum": 1
                    },
                    {
                        "type": "integer"
                    }
                ]
            },
            "no": {
                "not": [{
                    "type": "string"
                }]
            },
            "i": {
                "maximum": 10,
                "type": "integer"
            },
            "foo": {
                "type": "object",
                "a2": {
                    "type": "float"
                },
                "a1": {
                    "type": "integer"
                },
                "additionalProperties": True
            },
            "ss": {
                "$ref": "#/definitions/SimpleStruct"
            },
            "s": {
                "type": "string",
                "maxLength": 5
            },
            "enum": {
                "type": "enum",
                "values": [1,2,3]
            },
            "additionalProperties": True
    }
