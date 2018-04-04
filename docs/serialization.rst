===================
Serialization
===================

.. currentmodule:: typedpy

.. contents:: :local:

The Basics - Usage
==================

Typedpy allows to deserialize/ a JSON-like Python dict to an instance of a predefined :class:`Structure`,
as well serialize an instance of :class:`Structure` to a JSON-like dict.
The target class can have fields that are embedded structure or even class references.


See example below:

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


    def test_deserialization_and_serialization_with_many_types():
        source = {
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

        # Deserialization:
        example = deserialize_structure(Example, source)

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

        # Serialization
        result = serialize(example)
        assert result==source


**To convert the result of serialize() to JSON use:**

.. code-block:: py

   json.dumps(schema, indent=4)

Serialization to a JSON that is not an object
---------------------------------------------
If the structure is effectively a wrapper around a single field, Typedpy allows to serialize directly to the \
JSON representing only that field, using the "compact" flag. For example:

.. code-block:: py

    class Foo(Structure):
        s = Array[AnyOf[String, Number]]
        _additionalProperties = False

    foo = Foo(s=['abcde', 234])
    assert serialize(foo, compact=True)==['abcde', 234]

Deserialization of a non-object JSON
------------------------------------
If the JSON is not an object, and the target :class:`Structure` is a single field wrapper, then Typedpy \
tries to deserialize directly to that field. For example:

.. code-block:: py

    class Foo(Structure):
        i = Integer
        _additionalProperties = False

    data = 5

    example = deserialize_structure(Foo, data)
    assert example.i == 5


Limitations
-----------
#. Some complex fields have ambiguous serialized representation, for example: if a field can be an \Instance of some class A, or class B (e.g. :class:`AnyOf` [A, B])- the deserialization is not well defined. Such fields are unsupported.
#. For Set, Tuple - deserialization expects an array, serialization converts to array

Functions
=========

.. autofunction:: deserialize_structure

.. autofunction:: serialize


