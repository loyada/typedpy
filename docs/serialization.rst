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

Serialization of a Structure to a JSON that is not an object
============================================================
If the structure is effectively a wrapper around a single field, Typedpy allows to serialize directly to the \
JSON representing only that field, using the "compact" flag. For example:

.. code-block:: py

    class Foo(Structure):
        s = Array[AnyOf[String, Number]]
        _additional_properties = False

    foo = Foo(s=['abcde', 234])
    assert serialize(foo, compact=True)==['abcde', 234]
    assert serialize(foo.s) == ['abcde', 234]

Deserialization of a non-object JSON to a Structure
===================================================
If the JSON is not an object, and the target :class:`Structure` is a single field wrapper, then Typedpy \
tries to deserialize directly to that field. For example:

.. code-block:: py

    class Foo(Structure):
        i = Integer
        _additional_properties = False

    data = 5

    example = deserialize_structure(Foo, data)
    assert example.i == 5


.. _custom-serialization:

Serialization/Deserialization of a Field
========================================
Serialization
-------------
The best way to serialize an arbitrary Field is using the :meth:`serialize_field` function. This function
requires the first argument to be the Field definition (the Field definition has the information how to serialize).

However, in many common cases the original value has enough information for typedpy to know how to deserialize
it. These cases include the trivial types (i.e. str, int, float, bool), Structures and Structure-References, as well the values for the following
Typedpy fields: Array, Map, Enum. In such cases the :meth:`serialize` function provides a simpler API.

For example:

.. code-block:: py

    class Foo(Structure):
        a = String
        i = Integer

    class Bar(Structure):
        x = Float
        foos = Array[Foo]
        dt = DateTime


    assert serialize_field(Bar.foos, bar.foos)[0]['a'] == 'a'
    assert serialize_field(Array[Foo], bar.foos)[0]['a'] == 'a'

    # Simpler:
    assert serialize(bar.foos)[0]['a'] == 'a'

    # However, this will raise an Exception. Typedpy does not know how to serialize it automatically
    serialize(bar.dt)
    #  TypeError: serialize: Not a Structure or Field that with an obvious serialization


Deserialization
---------------
To deserialize a single field value directly, use :meth:`deserialize_single_field` .

For example:

.. code-block:: py

     class Foo(ImmutableStructure):
            a: String
            b: Optional[String]
            _ignore_none = True

    res = deserialize_single_field(Array[Foo], [{"a": "x", "b": None}, {"a": "y", "b": "xyz"}])
    assert res == [Foo(a="x"), Foo(a="y", b="xyz")]


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
    deserialized = Deserializer(target_class=Foo).deserialize(original, keep_undefined=False)
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
    deserialized = Deserializer(target_class=Blah).deserialize(original, keep_undefined=False)
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


Deserialization From Trusted Data
============================================
If we are serializing to a "simple" Structure, you can bypass Typedpy's sophisticated dynamic serialization and
instantiation, and directly create an instance of the wanted class.
This is useful when you are confident the data passed is valid, and performance is paramount.

The definition of a "simple" Structure, in this context, is:
* Serialization mapper, if exists, does not include function transformations.
* Fields can mapped directly to Json: None, str, int, float, bool, and lists of one of those.
* No nested dictionaries or Structures.
* Enum fields are supported!


The gain in performance is typically X15.

.. code-block:: python

    class Policy(ImmutableStructure):
        soft_limit: PositiveInt
        hard_limit: PositiveInt
        time_days: Optional[PositiveInt]
        codes: Array[int]

        _serialization_mapper = mappers.TO_CAMELCASE

    serialized = {
        "softLimit": 5,
        "hardLimit": 10,
        "timeDays": 2,
        "codes": [33,44,55],
    }

    # This will be executed much faster than a typical Typedpy deserialization
    policy = deserializer.deserialize(input_data=serialized, direct_trusted_mapping=True)


Note that deserializing this way bypasses any serialization mapper of the Structure. Also,
if the Structure is not "Simple" (as described above), the flat "direct_trusted_mapping" has no effect.





.. _serialization-classes:

Classes
=======
(starting at version 0.70)

.. autoclass:: FunctionCall

.. autoclass:: Serializer

.. autoclass:: Deserializer

.. autoclass:: HasTypes


Functions
=========

.. autofunction:: deserialize_structure

.. autofunction:: deserialize_single_field

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
        deserializer = Deserializer(target_class=Bar, {'numbers': 'i', 's': 'f'})
        serializer = Serializer(source=foo, mapper=mapper)

        return deserializer.deserialize(serializer.serialize(), keep_undefined=False)

    assert transform_foo_to_bar(Foo(f=5.5, i=999)) == Bar(numbers=[999], s='5.5')


Be aware that this is not a performant approach. Avoid it if speed is a major concern.


Deserialization Using a Discriminator Field
===========================================
Sometimes we want to determine to which Structure we deserialize to, based on a discriminator field in the input.
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
        deserialized = Deserializer(target_class=Bar).deserialize(serialized, keep_undefined=False)
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



Ignoring Fields When Serializing
--------------------------------
(since version 2.6.10)
Certain fields can be marked as DoNotSerialize. This would result in them not being serialized.
For example:

.. code-block:: python

   class Foo(Structure):
        a: int
        s: str

        _serialization_mapper = [{"a": DoNotSerialize}]

    assert Serializer(Foo(a=5, s="xyz")).serialize() == {"s": "xyz"}

As can be seen above, the "s" field is not serialized.



Chaining Mappers
----------------

Typedpy also allows chaining of serialization mappers. If you define _serialization_mapper
as a list, the mappers will be applied in order, and aggregate through inheritance.
For example:


.. code-block:: python

    class Foo(Structure):
        i: int
        s: str
        _serialization_mapper = {"i": "j", "s": "name"}

    class Bar(Foo):
        a: Array

        _serialization_mapper = [{"j": DoNotSerialize}, mappers.TO_LOWERCASE]
        _deserialization_mapper = [mappers.TO_LOWERCASE]

    deserialized = Deserializer(target_class=Bar).deserialize(
        {"J": 5, "A": [1, 2, 3], "NAME": "jon"}, keep_undefined=False
    )
    assert deserialized == Bar(i=5, a=[1, 2, 3], s="jon")
    assert Serializer(deserialized).serialize() == {"NAME": "jon", "A": [1, 2, 3]}


In the example above, the deseriazation mapper of Bar chains the one Foo and TO_LOWERCASE. The order
of the mappers is based on the MRO (inherited classes first).
If we follow the serialization mapper chaining for the "i" field, we see the stages:

1. i -> j
2. j -> don't serialize
3. to uppercase  - but this has no impact because of (2)


Conversely, the "s" field:

1. s -> name
2. no impact
3. name -> NAME


Serializing Additional Values Beyond Fields
===========================================
(from v2.9)

In certain cases, you might want to serialize Typepy structures so that the result includes other values in addition to
fields. For example, you may have a "Purchase" Structure class with all the line-items of the purchase and their price,
and also a calculated Python property of the total_amount that you want to include in the serialization.

For such cases, you can override the method Structure._additional_serialization().

This method returns a dict of additional values to be serialized. Each value is an expression or a function that does
not accept any parameters.
Here is a fairly comprehensive example from the unit tests:

.. code-block:: python

    class Foo(Structure):
        a: int
        s: str
        x = 1

        def double_a(self):
            return self.a * 2

        _serialization_mapper = [{"a": "b"}, mappers.TO_LOWERCASE]

        def _additional_serialization(self) -> dict:
            return {
                "double_a": self.double_a,   # a method (e.g. be a @property)
                "x": self.x,
                "triple_a": self.a * 3,     # an expression
                "y": [1, 2, 3],
                "z": lambda: Foo.x + self.a  # a function with no arguments
            }

    foo = Foo(a=5, s="xyz")
    serialized = Serializer(foo).serialize()
    assert serialized == {
        "B": 5,
        "S": "xyz",
        "double_a": 10,
        "x": 1,
        "triple_a": 15,
        "y": [1, 2, 3],
        "z": 6
    }

As seen in the example, the "additional serialization" is applied as the last step, after the serialization mappers were
already applied. In other words, the serialization mappers do not apply to the "additional serialization".


Adding Type Of Class To Serialization
=====================================
If you have a base class, such as Employee, and several classes that extend it, you might need to serialize a list
of Employees, adding to each employee its type. You could set this value explicitly, but this seems
like boilerplate code and error-prone.

Typedpy provides a small mixin to deal with this use-case:  :class:`HasTypes`. It adds to the serialized representation
a "type" attribute, with the name of the subclass.

To illustrate the usage, examine the following snippet:

.. code-block:: python

   class Employee(Structure, HasTypes):
        name: str

    class Engineer(Employee):
        pass

    class Sales(Employee):
        pass

    class Marketer(Employee):
        pass

    class Firm(Structure):
        employees: Array[Employee]

    firm = Firm(employees=[
        Engineer(name="john"),
        Marketer(name="rob"),
        Sales(name="joe")
    ])

    assert Serializer(firm).serialize() == {
        "employees": [
            {"type": "engineer", "name": "john"},
            {"type": "marketer", "name": "rob"},
            {"type": "sales", "name": "joe"},
        ]
    }


Force a Field To Be Set As A Constant During Deserialization
============================================================
(new in 2.13.0)
Imagine a use-case in which you have an abstract base class "Car", and several cars that inherit from it. One of
the fields you might want to have is "maker":

.. code-block:: python

    class Car(AbstractStructure):
        maker: str
        ...

    class SubaruOutback(Car):
        ...

    class AcuraMVX(Car):
        ...


When you deserialize SubaruOutback or AcuraMVX, you should set the "maker" explicitly to a predefined value.
Typedpy supports it, by defining "Constant" in the serialization mapper (similar to Version Mapping). See below:

.. code-block:: python

    class SubaruOutback(Car):
        ...

        _deserialization_mapper = {"maker": Constant("Subaru")}


    class AcuraMVX(Car):
        ...

        _deserialization_mapper = {"maker": Constant("Acura")}

This means that the field "maker" will ignore the input to the deserializer, and always set to the value defined
in the mapper.


Enums Serialization/Deserialization
===================================
Consider the example:

.. code-block:: python

   class Foo(enum.Enum):
        A = 1
        B = 2
        C = 3

    class Bar(Structure):
        e: Enum[Foo]
        e_value: Enum(values=Foo, serialization_by_value=True)

        _required = []

    assert Serializer(Bar(e_value=Foo.A)).serialize() == {"e_value": 1}
    assert Serializer(Bar(e=Foo.A)).serialize() == {"e": "A"}

By default, an enum field is serialized to a string with the *name* of the enum entry. This is why when we serialized
"e" in the example above, the resulting value is "A".
Serialization by the *value* of the enum is achieved by setting the serialization_by_value flag, as in the field
"e_value" above.

The same is true for deserialization.


Fast Serialization
==================
Typedpy offers a significantly faster version of serialization. Using internal profiling it is roughly 4-5 times faster.

However, it requires more setup. First, you need to mark the Structure class by FastSerializable.

Then, tell Typedpy to implement an optimized serializer, by calling create_serializer(<your class>). For example:


.. code-block:: python

    from typedpy import Structure, FastSerializable, Integer, create_serializer, mappers

    class Foo(Structure, FastSerializable):
        a: list[Integer(max=5)]
        b: str
        _required = []
        _serialization_mapper = mappers.TO_LOWERCASE

    # optional: if you want to create the serializer before Foo is used.
    # Otherwise, it creates the serializer on the first instantiation
    create_serializer(Foo)

    foo = Foo(a=[1, 5])
    serialized = foo.serialize()
    assert serialized = {"A": [1, 5], "b": None}

In case you implement your own custom Field classes, they can include a custom serialize(value) method.
Fast serialization can be used for the vast majority of the cases, including serialization mappers, but does not
support the following:


#. Nested mappers. I.E: a mapper that looks like {"foo._mapper": {....}}"
#. Function mappers
#. Serialize class type automatically - ie. :class:`HasTypes`
#. Serialize attributes that are not Typedpy fields
#. providing custom mappers when calling serialize()


Requirements/Limitations:

#. All Structures in the hierarchy implement FastSerializable. Typically this is done by calling create_serializer, or
   or automatically, during first instantiation.
#. Any custom Field classes should implement the serialize() method.
#. All mappers must be in the definition of the Structures.
#. No mapper to Typedpy Constant in custom serialization mapper of the class


Instead of support of the "compact" (see above) flag in the serialize() call, you provide it to create_serializer().
For example:

.. code-block:: python

    class Foo(Structure, FastSerializable):
        s = Array[AnyOf[String, Number]]
        _additionalProperties = False

    create_serializer(Foo, compact=True)

    foo = Foo(s=["abcde", 234])
    assert foo.serialize() == ["abcde", 234]


To control whether or not None values are serialized, use the optional flag "serialize_none" when creating
the serializer, as such:


.. code-block:: python

    create_serializer(Foo, serialize_none = True)