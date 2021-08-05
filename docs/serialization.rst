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
=============================================
If the structure is effectively a wrapper around a single field, Typedpy allows to serialize directly to the \
JSON representing only that field, using the "compact" flag. For example:

.. code-block:: py

    class Foo(Structure):
        s = Array[AnyOf[String, Number]]
        _additionalProperties = False

    foo = Foo(s=['abcde', 234])
    assert serialize(foo, compact=True)==['abcde', 234]
    assert serialize(foo.s) == ['abcde', 234]

Deserialization of a non-object JSON
====================================
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
====================
Sometimes you might want to define your own serialization or deserialization of a field. \
For example: suppose you have a datetime object in one of the properties. You want to serialize/deserialize \
it using a custom format. For that, you can inherit from  :class:`SerializableField` \

(for an alternative solution, see :ref:`custom-mapping` )
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


.. _custom-mapping:

Custom mapping in the deserialization
=====================================

What if there is no exact match between the serialized data and our Structure? \
Typedpy supports passing a custom mapper to the deserializer, so that the user can define how to deserialize each attribute. \
The mapper is a  dictionary, in which the key is the attribute name, and the value can be either a key in the source dict, \
or a :class:`FunctionCall` (a function and a list of keys in the source dict that are passed to the function). \

* When the mapping is from source key to attribute, nested keys are supported as well, using dot notation (i.e. "xxx.yyy.zzz").

* When the mapping is using a function call, the provided function is expected to return the value that will be used as the input of the deserialization.

* To determine mapping for an embedded field/structure, use the notation: "<field name>._mapper". See example below.

An example can demonstrate the usage:


.. code-block:: python

    class Foo(Structure):
        m = Map
        s = String
        i = Integer

    mapper = {
        "m": "a.b",
        "s": FunctionCall(func=lambda x: f'the string is {x}', args=['name.first']),
        'i': FunctionCall(func=operator.add, args=['i', 'j'])
    }

    foo = deserialize_structure(Foo,
                                {
                                    'a': {'b': {'x': 1, 'y': 2}},
                                    'name': {'first': 'Joe', 'last': 'smith'},
                                    'i': 3,
                                    'j': 4
                                },
                                mapper=mapper,
                                keep_undefined=False)
    # keep_undefined=False ensures it does not also create attributes a, name, j in the deserialized instance
    assert foo == Foo(i=7, m={'x': 1, 'y': 2}, s='the string is Joe')

An example of mapping of a field item within a list:

.. code-block:: python

    class Foo(Structure):
        a = String
        i = Integer

    class Bar(Structure):
        wrapped = Array[Foo]

    mapper = {'wrapped._mapper': {'a': 'aaa', 'i': 'iii'}, 'wrapped': 'other'}
    deserializer = Deserializer(target_class=Bar, mapper=mapper)
    deserialized = deserializer.deserialize(
        {
            'other': [
                {'aaa': 'string1', 'iii': 1},
                {'aaa': 'string2', 'iii': 2}
            ]
        },
        keep_undefined=False)

    assert deserialized == Bar(wrapped=[Foo(a='string1', i=1), Foo(a='string2', i=2)])

An example of nested mapping:

.. code-block:: python

    class Foo(Structure):
        a = String
        i = Integer
        s = StructureReference(st=String, arr=Array)

    mapper = {
        'a': 'aaa',
        'i': 'iii',
        's._mapper': {"arr": FunctionCall(func=lambda x: x * 3, args=['xxx'])}
    }
    deserializer = Deserializer(target_class=Foo, mapper=mapper)
    deserialized = deserializer.deserialize({
            'aaa': 'string',
            'iii': 1,
            's': {'st': 'string', 'xxx': [1, 2, 3]}},
        keep_undefined=False)

    assert deserialized == Foo(a='string', i=1, s={'st': 'string', 'arr': [1, 2, 3, 1, 2, 3, 1, 2, 3]})


Custom mapping in the serialization
===================================
Similarly, you can provide a mapper when serializing. This mapper is a bit different  -  to define a nested mapping, \
it uses the key of the form "field-name._mapper". It supports nested fields as long as they are not in a Map. \
A simple example of changing the field name:

.. code-block:: python

    class Foo(Structure):
        a = String
        i = Integer

    foo = Foo(a='string', i=1)
    mapper = {'a': 'aaa', 'i': 'iii'}
    assert serialize(foo, mapper=mapper) == {'aaa': 'string', 'iii': 1}


An simple example of transformation:

.. code-block:: python

    def my_func(): pass

    class Foo(Structure):
        function = Function
        i = Integer

    foo = Foo(function=my_func, i=1)
    mapper = {
        'function': FunctionCall(func=lambda f: f.__name__),
        'i': FunctionCall(func=lambda x: x + 5)
    }
    assert serialize(foo, mapper=mapper) == {'function': 'my_func', 'i': 6}


An example of nested mapping in an array field:

.. code-block:: python

    class Foo(Structure):
        a = String
        i = Integer

    class Bar(Structure):
        wrapped = Array[Foo]

    bar = Bar(wrapped=[Foo(a='string1', i=1), Foo(a='string2', i=2)])
    mapper = {'wrapped._mapper': {'a': 'aaa', 'i': 'iii'}, 'wrapped': 'other'}
    assert serialize(bar, mapper=mapper) ==
           {'other': [{'aaa': 'string1', 'iii': 1}, {'aaa': 'string2', 'iii': 2}]}


An example of a deep nested mapper:

.. code-block:: python

  class Foo(Structure):
        a = String
        i = Integer

    class Bar(Structure):
        foo = Foo
        array = Array

    class Example(Structure):
        bar = Bar
        number = Integer

    example = Example(number=1,
                      bar=Bar(foo=Foo(a="string", i=5), array=[1, 2])
                      )
    # our mapper doubles the value of the field  bar->foo->i
    mapper = {'bar._mapper': {'foo._mapper': {"i": FunctionCall(func=lambda x: x * 2)}}}
    serialized = serialize(example, mapper=mapper)
    assert serialized == \
           {
               "number": 1,
               "bar":
                   {
                       "foo": {
                           "a": "string",
                           "i": 10  #   result of mapping: 5*2
                       },
                       "array": [1, 2]
                   }
           }


Custom Mappers as Part of the Class Definitions
================================================
using "_serialization_mapper" and "_deserialization_mappers" allow to define custom mappers within the class definition.
These will also aggregate through inheritance.
In case the serialization and deserialization mappers are the same, just use "_serialization_mapper". If they differ, \
for example: if you use a functional transformation in the serialization and need to apply the opposite function when \
deserializing, use also "_deserialization_mapper".

You can also apply multiple mappers serially, as the example below:

For example:

.. code-block:: python

    class Foo(Structure):
        a: int
        s: str

        _serialization_mapper = [{"a": "b"}, mappers.TO_LOWERCASE]

    original = {"B": 5, "S": "xyz"}
    deserialized = Deserializer(Foo).deserialize(original, keep_undefined=False)
    assert deserialized == Foo(a=5, s="xyz")
    serialized = Serializer(deserialized).serialize()
    assert serialized == original


Another, more involved mapping:

.. code-block:: python

    class Foo(Structure):
        xyz: Array
        i: int
        _serialization_mapper = {"i": "j"}

    class Bar(Foo):
        a: Array

        _serialization_mapper = mappers.TO_LOWERCASE

    class Blah(Bar):
        s: str
        foo: Foo
        _serialization_mapper = {}
        _deserialization_mapper = {"S": FunctionCall(func=lambda x: x * 2)}

    original = {
        "S": "abc",
        "FOO": {
            "XYZ": [1, 2],
            "J": 5
        },
        "A": [7, 6, 5, 4],
        "XYZ": [1, 4],
        "J": 9
    }
    deserialized = Deserializer(Blah).deserialize(original, keep_undefined=False)
    assert deserialized == Blah(
        s="abcabc",
        foo=Foo(i=5, xyz=[1, 2]),
        xyz=[1, 4],
        i=9,
        a=[7, 6, 5, 4]
    )
    serialized = Serializer(deserialized).serialize()

    # Note, Typedpy will not magically reverse your custom mapping function, and
    # is limited when combining function and key transformation,
    # thus the "S" field below.
    assert serialized == {**original, "S": "abcabc"}


Strict Serialization and Deserialization API
============================================
Starting at version 0.70, Typedpy provides a strict API, aligned with the principles of Typedpy. This API uses Typedpy \
classes for serializer and deserializer. It is easier to understand, and catches obvious errors in the mapper early. \
This is the preferable API to use. \
There are 2 classes provided: :class:`Serializer` and :class:`Deserializer`.   \
The Serializer class accepts the instance of the structure to be serialized, while the Deserializer accepts the target \
Structure class to be deserialized to.  \
Both the Deserializer and Serializer accept an optional mapper. The mapper works similarly to the one described above \
but it is a strict Typedpy Field, and the classes are self validating, so that it is impossible to have an instance \
which is obviously invalid. \
See below for the documentation of the :ref:`serialization-classes` \

There are plenty of examples for usage here: \
`Serialization examples - <https://github.com/loyada/typedpy/tree/master/tests/test_serialization.py>`_ \
`Deserialization examples - <https://github.com/loyada/typedpy/tree/master/tests/test_deserialization.py>`_ \


Examples of invalid definitions that are caught immediately: \

.. code-block:: python

    class Foo(Structure):
        f = Float
        i = Integer

    foo_instance = Foo(f=5.5, i=999)
    # we define a mapper that has an invalid argument 'x', since 'x' is not an attribute of Foo.
    mapper = {
        'f': FunctionCall(func=lambda f: [int(f)], args=['i', 'x']),
        'i': FunctionCall(func=lambda x: str(x), args=['f'])
    }

    # the following will raise a ValueError: "Mapper[f] has a function call with an invalid argument: x"
    Serializer(foo, mapper=mapper)

    class Bar(Structure):
        m = Map
        s = String
        i = Integer

    #this is an invalid mapper, since the key "xyz" is not an attribute in Bar
    mapper = {
        "xyz": "a.b",
        "s": FunctionCall(func=lambda x: f'the string is {x}', args=['name.first']),
        'i': FunctionCall(func=operator.add, args=['i', 'j'])
    }

    # the following will raise a ValueError: Invalid key in mapper for class Bar: xyz
    Deserializer(target_class=Bar, mapper=mapper)

    # the following will raise a TypeError, since the Mapper types are wrong
    Deserializer(target_class=Bar, mapper= {'s': [1,2,3] })


Here is a valid usage example, referring to the same Bar class defined in the previous example: \

.. code-block:: python

    mapper = {
        "m": "a.b",
        "s": FunctionCall(func=lambda x: f'the string is {x}', args=['name.first']),
        'i': FunctionCall(func=operator.add, args=['i', 'j'])
    }

    deserializer = Deserializer(target_class=Bar, mapper=mapper)

    bar = deserializer.deserialize({
            'a': {'b': {'x': 1, 'y': 2}},
            'name': {'first': 'Joe', 'last': 'smith'},
            'i': 3,
            'j': 4
        }, keep_undefined=False)

    assert bar == Bar(i=7, m={'x': 1, 'y': 2}, s='the string is Joe')


.. _serialization-classes:

Classes
=======
(starting at version 0.70)

.. autoclass:: FunctionCall

.. autoclass:: Serializer

.. autoclass:: Deserializer


Functions
=========

.. autofunction:: deserialize_structure

.. autofunction:: serialize

.. autofunction:: serialize_field


Transformations
===============
Serializer and deserializers can be used with mappers to transform one dictionary to another, or one
Structure to another.

Here is a contrived example:

.. code-block:: python

    class Foo(Structure):
        f = Float
        i = Integer

    class Bar(Structure):
        numbers = Array[Integer]
        s = String

    def transform_foo_to_bar(foo: Foo) -> Bar:
        mapper = {
            'i': FunctionCall(func=lambda f: [int(f)], args=['i']),
            'f': FunctionCall(func=lambda x: str(x), args=['f'])
        }
        deserializer = Deserializer(Bar, {'numbers': 'i', 's': 'f'})
        serializer = Serializer(source=foo, mapper=mapper)

        return deserializer.deserialize(serializer.serialize(), keep_undefined=False)

    assert transform_foo_to_bar(Foo(f=5.5, i=999)) == Bar(numbers=[999], s='5.5')


Be aware that this is not a performant approach. Avoid it if speed is a major concern.


Deserialization Using a Discriminator Field
===========================================
Sometimes we want to determine to which Structure we deserialize, based on a discriminator field in the input.
This is supported in Typedpy. Consider the following:

.. code-block:: python

    class Foo(Structure):
        i: int


    class Foo1(Foo):
        a: str


    class Foo2(Foo):
        a: int


    class Bar(Structure):
        t: str
        f: Array[Integer]
        foo: Foo

        _serialization_mapper = {
            "t": "type",
            "foo": FunctionCall(func=deserializer_by_discriminator({
                "1": Foo1,
                "2": Foo2,
            }),
                args=["type", "x.foo"])
        }

     serialized = {
            "type": "1",
            "f": [1, 2, 3],
            "x": {
                "foo": {
                    "a": "xyz",
                    "i": 9
                }
            }
        }
        deserialized = Deserializer(Bar).deserialize(serialized, keep_undefined=False)
        assert deserialized == Bar(t="1", f=[1, 2, 3], foo=Foo1(a="xyz", i=9))

Here, we determine how to deserialize the content of serialized["x"]["foo"], based on the value of "type".
The function factory "deserializer_by_discriminator" is included in Typedpy, and creates deserialization function.
As can be seen in the example, the first parameter to it is the discriminator key, and the second is the key of
the content to be serialized.

* New in 2.4.5

Predefined Mappers
==================
There are two predefined mappers:
* TO_CAMELCASE - convert between python snake-case and the more common naming in JSON, of camel-case
* TO_LOWERCASE - convert between field names in lower case, and the serialized representation in upper case (common in configuration)

An example:

.. code-block:: python

    from typedpy import mappers

    class Bar(Structure):
        i: int
        f: float

    class Foo(Structure):
        abc: str
        xxx_yyy: str
        bar: Bar

        _serialization_mapper = mappers.TO_LOWERCASE

    foo = deserialize_structure(Foo, {'ABC': 'aaa', 'XXX_YYY': 'bbb', 'BAR': {'I': 1, 'F': 1.5}})
    assert foo == Foo(abc='aaa', xxx_yyy='bbb', bar=Bar(i=1, f=1.5))




Support for Versioning
======================
The use-case for support for versioning Typedpy addresses is deserializing different versions of the dictionary representing \
the structure to match the latest Structure definition.

For example, suppose you saved a JSON object that adheres to some strict schema, and occasionally that schema had to evolve \
to include new fields, or update existing ones. When you read it again, you always want to map to the latest schema, which \
is what you are currently using.


The requirement: Typedpy expects the dictionary to have a "version" field, that has increasing consecutive integer values, \
starting from 1.
Next, you need to provide a list of mappers. Each mapper defines how to convert from the corresponding version to the next.
These mappers are, in general, similar to the regular "serialization mappers" of Typedpy, but they add 2 new features:

1. Constant(val) - the value is a constant. This is useful when you introduced a new field in a more recent version and
   you want to define that when converting older versions, we need to populate it with a default value.

2. Deleted - The newer version no longer has this field, and it should be dropped


Typedpy has two types of API's to handle it.

Low-Level API
-------------

Example of usage:

.. code-block:: python

    versions_mapping = [
            # Mapping from version 1 to 2
        {
            "j": Constant(100),
            "old_bar._mapper": {
                "a": FunctionCall(func=lambda x: [i * 2 for i in x], args=["a"]),
            },
            "old_m": Constant({"abc": "xyz"})
        },

            # mapping from version 2 to 3
        {
            "old_bar._mapper": {
                "s": "sss",
                "sss": Deleted
            },
            "bar": "old_bar",
            "m": "old_m",
            "old_m": Deleted,
            "old_bar": Deleted,
        },

            # mapping from version 3 to 4
        {
            "i": FunctionCall(func=lambda x: x * 100, args=["i"])
        }
    ]

    in_version_1 = {
        "version": 1,
        "old_bar": {
            "a": [5, 8, 2],
            "sss": "john",
        },
        "i": 2,
        "old_m": {"a": "aa", "b": "bb"}
    }

    assert convert_dict(in_version_1, versions_mapping) == {
        "version": 4,
        "bar": {
            "a": [10, 16, 4],
            "s": "john",
        },
        "i": 200,
        "j": 100,
        "m": {"abc": "xyz"},
    }

*Explanation*: The function convert_dict will apply all the applicable mappings based on the version of the input. In
this case, it needs to replay all the mapping, since the raw input is at version 1.

To further illustrate, let's follow the steps.

After the first mapper (i.e. version 2), the input looks like:

.. code-block:: python

    {'version': 2, 'old_bar': {'a': [10, 16, 4], 'sss': 'john'}, 'i': 2, 'old_m': {'abc': 'xyz'}, 'j': 100}


After the the second mapper (i.e. version 3), the input looks like:

.. code-block:: python

    {'version': 3, 'i': 2, 'j': 100, 'bar': {'a': [10, 16, 4], 's': 'john'}, 'm': {'abc': 'xyz'}}


And finally, after the last mapper, it looks like:

.. code-block:: python

    {'version': 4, 'i': 200, 'j': 100, 'bar': {'a': [10, 16, 4], 's': 'john'}, 'm': {'abc': 'xyz'}}



High-Level API
--------------

Typedpy defines a special Structure that is effectively a marker for a versioned structure: :class:`Versioned`

.. autoclass:: Versioned


The example below clarifies how to use :class:`Versioned` together with deserializer.

.. code-block:: python


    class Foo(Versioned, ImmutableStructure):
        bar: Bar
        i: Integer
        j: Integer
        m: Map[String, String]

        _versions_mapping = [
            {   # version 1 -> 2
                "j": Constant(100),
                "old_bar._mapper": {
                    "a": FunctionCall(func=lambda x: [i * 2 for i in x], args=["a"]),
                },
                "old_m": Constant({"abc": "xyz"})
            },

            {   # version 2 -> 3
                "old_bar._mapper": {
                    "s": "sss",
                    "sss": Deleted
                },
                "bar": "old_bar",
                "m": "old_m",
                "old_m": Deleted,
                "old_bar": Deleted,
            },

            {   # version 3 -> 4
                "i": FunctionCall(func=lambda x: x * 100, args=["i"])
            }

        ]


    # Once defined, the deserializer applies the versions conversion as the first step.
    # For example:
    in_version_1 = {
        "version": 1,
        "old_bar": {
            "a": [5, 8, 2],
            "sss": "john",
        },
        "i": 2,
        "old_m": {"a": "aa", "b": "bb"}
    }
    assert Deserializer(Foo).deserialize(in_version_1) == Foo(
        bar=Bar(a=[10, 16, 4], s="john"),
        m={"abc": "xyz"},
        i=200,
        j=100,
        version=4
    )

