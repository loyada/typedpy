===================
Serialization
===================

.. currentmodule:: typedpy

.. contents:: :local:

The Basics - Usage
==================

Typedpy allows to deserialize a JSON-like Python dict to an instance of a predefined :class:`Structure`,
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


Though the above example does not show it, the deserializer also supports the following:

* A field that can be anything, using the Field type :class:`Anything`

* All the built in collections are fully supported, for example:  a = Array[Map[String, Integer]] is supported

* :class:`AnyOf`, :class:`OneOf`, :class:`NotField`, :class:`AllOf` are fully supported, including embedded structures in them. For example, if you had a structure Foo, the following is supported: p = Set[AnyOf[Foo, Array[Foo], String]]

* In case of an error in the input data, deserialize_structure() will raise an exception with the exact description of the problem.


**To convert the result of serialize() to JSON, use:**

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


.. _custom-serialization:

Custom Serialization
--------------------
Sometimes you might want to define your own serialization or deserialization of a field. \
For example: suppose you have a datetime object in one of the properties. You want to serialize/deserialize \
it using a custom format. For that, you can inherit from  :class:`SerializableField`

Example of custom deserialization:

.. code-block:: python

    class MySerializable(Field, SerializableField):
        def __init__(self, *args, some_param="xxx", **kwargs):
            self._some_param = some_param
            super().__init__(*args, **kwargs)

        def deserialize(self, value):
            return {"mykey": "my custom deserialization: {}, {}".format(self._some_param, str(value))}

         def serialize(self, value):
            return 123

    class Foo(Structure):
        d = Array[MySerializable(some_param="abcde")]
        i = Integer

    deserialized = deserialize_structure(Foo, {'d': ["191204", "191205"], 'i': 3})

    assert deserialized == Foo(i=3, d=[{'mykey': 'my custom deserialization: abcde, 191204'},
                                       {'mykey': 'my custom deserialization: abcde, 191205'}])

    assert serialize(deserialized) == {'d': [123, 123], 'i': 3}



Limitations and Guidance
------------------------
* For Set, Tuple - deserialization expects an array, serialization converts to array (set and tuple are not part of JSON)

* If you have a field that you want to assign as a blob, without any validation, use :class:`Anything` . When seriaizing a property of type :class:`Anything`, however, it is not guaranteed to work in all cases, since you can literaly asign it to anything without any validation, and Typedpy has no knowledge of what is supposed to be there. For example: suppose you assign some controller object to the property. Typedpy will allow it, since it is an Anything field, but has no idea how to serializa such an object.

* If you create a completely new field type, that is not based on the predefined classes in Typedpy, it is not guaranteed to be supported. For example - if you define a custom field type using :func:`create_typed_field`, it is not supported



Functions
=========

.. autofunction:: deserialize_structure

.. autofunction:: serialize


