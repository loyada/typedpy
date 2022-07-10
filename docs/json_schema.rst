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
        _additional_properties = False

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

In the example above, if '_required' was [], or _additional_properties was True, then the schema was an object with
a single property 'arr', as usual.

Schema mapping beyond the "basic" Types
---------------------------------------
To support custom Field types mapping, you need to implement 2 methods in the Field class: to_json_schema, and
from_json_schema. Here is an example from Typedpy:


.. code-block:: py

    class IPV4(String):
        # skipping some code....

        @classmethod
        def to_json_schema(cls) -> dict:
            return {"type": "string", "format": "ipv4"}

        @classmethod
        def from_json_schema(cls, schema: dict):
            return "IPV4()" if schema == IPV4.to_json_schema() else None



#.  to_json_schema - returns the schema for this field.
#.  from_json_schema - accepts the schema and returns the string for the code needed to instantiate the Field. If it
    does not match, it should return None.
#.  When converting from schema to code, the optional parameter "additional_fields" should have a list of all the classes
    with custom mapping


Limitations and Comments
------------------------
#. Not all the details of JSON schema are supported - but most of the common ones are.
#. Only the Field types that map to JSON Schema Draft 4 are inherently supported. This means that if you add a new
   custom Field class, you need to use the method described above.
#. Set and Tuple fields are mapped to array types when converting code to schema
#. Regarding JSON pointers(i.e. "$ref") - only pointers that point to an object under "#/definitions/" are supported


Examples
--------
Take a look at the many tests `here <https://github.com/loyada/typedpy/blob/e0505f40fefcb1c49e5e65563d4739ae1ea2c5b3/tests/schema_mapping/test_json_schema_code_mapping.py#L67>`_ .

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

