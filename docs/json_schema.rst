===================
JSON Schema Mapping
===================

.. currentmodule:: typedpy

.. contents:: :local:

The Basics - Usage
==================

Typedpy allows to map a json draft4 schema to code. This code can be saved to a .py file (recommended) or executed dynamically.
It supposts references to schema definitions, It also creates definitions whenever a Structure is being referenced.
Mapping a JSON schema to code, inherently provides schema validation when the generated classes are used.

.. code-block:: py

    from typedpy import schema_definitions_to_code, schema_to_struct_code, write_code_from_schema
    from typedpy.structures import *
    from typedpy.fields import *

    definitions = {
    "SimpleStruct": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "pattern": "[A-Za-z]+$",
                "maxLength": 8
            }
        },
        "required": [
            "name"
        ],
        "additionalProperties": True
        }
    }

    schema = {
        "type": "object",
        "description": "This is a test of schema mapping",
        "properties": {
            "foo": {
                "type": "object",
                "properties": {
                    "a2": {
                        "type": "float"
                    },
                    "a1": {
                        "type": "integer"
                    }
                },
                "required": [
                    "a2",
                    "a1"
                ],
                "additionalProperties": True
            },
            "ss": {
                "$ref": "#/definitions/SimpleStruct"
            },
            "enum": {
                "enum": [
                    1,
                    2,
                    3
                ]
            },
            "s": {
                "maxLength": 5,
                "type": "string"
            },
            "i": {
                "type": "integer",
                "maximum": 10
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
            "a": {
            "type": "array",
                "items": [
                    {
                        "type": "integer",
                        "multiplesOf": 5
                    },
                    {
                        "type": "number"
                    }
                ]
            }
        },
        "required": [
            "foo",
            "ss",
            "enum",
            "s",
            "i",
            "all",
            "a"
        ],
        "additionalProperties": True,
    }

    definitions_code = schema_definitions_to_code(definitions)
    exec(definitions_code, globals())

    struct_code = schema_to_struct_code('Duba', schema, definitions)
    exec(struct_code, globals())
    duba = Duba(
        foo = {'a1': 5, 'a2': 1.5},
        ss = SimpleStruct(name = 'abc'),
        enum = 2,
        s = "xyz",
        i = 10,
        all = 6,
        a = [10, 3]
    )
    assert duba.ss.name == 'abc'

    # Alternatively, and preferable, save it to a file:
    write_code_from_schema(schema, definitions, "generated_sample.py", "Poo")
    # Now we can load and use it:
    from generated_sample import Poo, SimpleStruct


Non-object top-level schemas are also supported, using a "field wrapper". A field wrapper Structure \
is a Structure that contains a single, required, field, and does not allow any other property (i.e. _additionalProperties = False).
For example:

For example:

.. code-block:: py

    class Foo(Structure):
        arr = Array(minItems=2)
        _required = ['arr']
        _additionalProperties = False

    schema, definitions = structure_to_schema(Foo, {})
    assert schema == {
        "type": "array",
        "minItems": 2
    }

    # And the back to a Structure...
    struct_code = schema_to_struct_code('Bar', schema, {})
    exec(struct_code, globals())

    bar = Bar([1,2,3])
    assert bar.wrapped[2] == 3

In the example above, if '_required' was [], or _additionalProperties was True, then the schema was an object with
a single property 'arr', as usual.


Limitations and Comments
------------------------
#. JSON schema's String formatters are unsupported
#. Only JSON Schema Draft 4 is supported. Draft 3/6/7 are unsupported
#. Only the Field types that map to JSON Schema Draft 4 are supported. This means that if you add a new custom Field
   class, it is currently unsupported, since the API does not include additional custom mappers.
#. Set and Tuple fields are mapped to array types when converting code to schema
#. Regarding JSON pointers(i.e. "$ref") - only pointers that point to an object under "#/definitions/" are supported


Functions
=========

Code to schema
--------------

.. autofunction:: structure_to_schema

Keep in mind that in order to print a JSON schema (as opposed to a Python dict), you need to do something like:

.. code-block:: py

    print(json.dumps(schema, indent=4))

Schema to code
--------------
.. autofunction:: schema_definitions_to_code

.. autofunction:: schema_to_struct_code

.. autofunction:: write_code_from_schema

