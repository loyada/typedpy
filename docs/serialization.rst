===================
Serialization
===================

.. currentmodule:: typedpy

.. contents:: :local:

The Basics - Usage
==================

Typedpy allows to deserialize a JSON-like Python dict to an instance of a predefined :class:`Structure`.
The target class can have fields that are embedded structure or even class references. See example
Below:

.. code-block:: py

    class SimpleStruct(Structure):
        name = String(pattern='[A-Za-z]+$', maxLength=8)

    class Example(Structure):
        i = Integer(maximum=10)
        s = String(maxLength=5)
        array = Array[Integer(multiplesOf=5), Number]
        embedded = StructureReference(a1 = Integer(), a2=Float())
        simplestruct = SimpleStruct
        all = AllOf[Number, Integer]
        enum = Enum(values=[1,2,3])


    def test_successful_deserialization_with_many_types():
        data = {
            'i': 5,
            's': 'test',
            'array': [10, 7],
            'embedded': {
                'a1': 8,
                'a2': 0.5
            },
            'simplestruct': {
                'name': 'danny'
            },
            'all': 5,
            'enum': 3
        }
        example = deserialize_structure(Example, data)
        assert example == Example(
            i = 5,
            s = 'test',
            array = [10,7],
            embedded = {
                'a1': 8,
                'a2': 0.5
            },
            simplestruct = SimpleStruct(name = 'danny'),
            all = 5,
            enum = 3
        )



Limitations
-----------
#. Some complex fields can have ambiguous serialized representation, for example: if a field can be an Instance of
some class A, or class B (e.g. :class:`AnyOf`[Foo, Bar])- the deserialization is not well defined. Such
fields are unsupported.
#. Set is unsupported, since it does not exist in JSON

Functions
=========

Code to schema
--------------
.. autofunction:: write_code_from_schema

Keep in mind that in order to print a JSON schema (as opposed to a Python dict), you need to do something like:

.. code-block:: py

    print(json.dumps(schema, indent=4))

Schema to code
--------------
.. autofunction:: schema_definitions_to_code

.. autofunction:: schema_to_struct_code

.. autofunction:: structure_to_schema

