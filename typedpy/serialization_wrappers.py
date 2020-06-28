from typedpy import Structure
from typedpy.fields import StructureClass, Map, String, OneOf
from typedpy.serialization import FunctionCall, get_all_fields_by_name, deserialize_structure, serialize


class Deserializer(Structure):
    """
        A high level API for a deserializer: from a dict or anything else that could be sent as a JSON, to
        a :class:`Structure`.
        The advantage of this over the lower level function is that it is more explicit and self-validating.
        In other words, it prevents the user from creating an invalid mapper.

        Arguments:
            target_class(:class:`StructureClass`):
                A class extending the abstract :class:`Structure` that this deserializer is build for.
                Example:

                .. code-block:: python

                    class Foo(Structure):
                        id = Integer
                        name = String

                   Deserializer(target_class=Foo)


            mapper(dict): optional
                The key is the target attribute name. The value can either be a path of the value in the source dict
                using dot notation, for example: "aaa.bbb", or a :class:`FunctionCall`. In the latter case,
                the function is the used to preprocess the input prior to deserialization/validation.
                The args attribute in the function call is optional. If non provided, the input to the function is
                the value with the same key. Otherwise it is the keys of the values in the input that are injected
                to the provided function. See working examples in the tests link above.
                This class will ensure that the mapper is a valid one for its target_class.
                Example:

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


    """

    target_class = StructureClass
    mapper = Map[String, OneOf[String, FunctionCall]]

    _required = ['target_class']

    def __validate__(self):
        valid_keys = set(get_all_fields_by_name(self.target_class).keys())
        if self.mapper:
            for key in self.mapper:
                if key not in valid_keys:
                    raise ValueError(
                        "Invalid key in mapper for class {}: {}. Keys must be one of the class fields.".format(
                            self.target_class.__name__, key))

    def deserialize(self, input, keep_undefined=True):
        return deserialize_structure(self.target_class,
                                     input,
                                     mapper=self.mapper,
                                     keep_undefined=keep_undefined
                                     )


class Serializer(Structure):
    """
           A high level API for a serializer: from an instance of :class:`Structure`, to something that can be sent as a Json
           (usually a dict). The advantage of this over the lower level function is that it is more explicit and
           self-validating. In other words, it prevents the user from creating an invalid mapper.

           Arguments:
               source(:class:`StructureClass`):
                   A class extending the abstract :class:`Structure` that this deserializer is build for.
                   Example:

                   .. code-block:: python

                       class Foo(Structure):
                           id = Integer
                           name = String

                      Deserializer(target_class=Foo)


               mapper(dict): optional
                   The key is the target attribute name. The value can either be a path of the value in the source dict
                   using dot notation, for example: "aaa.bbb", or a :class:`FunctionCall`. In the latter case,
                   the function is the used to preprocess the input prior to deserialization/validation. \
                   The args attribute in the function call is optional. If non provided, the input to the function is
                   the value with the same key. Otherwise it is the keys of the values in the input that are injected
                   to the provided function. \
                   See working examples in the tests link above. \
                   This class will ensure that the mapper is a valid one for its target_class.
                   Example:

                   .. code-block:: python

                        class Foo(Structure):
                           m = Map
                           s = String
                           i = Integer

                        foo = Foo(f=5.5, i=999)
                        mapper = {
                           "m": "a.b",
                           "s": FunctionCall(func=lambda x: f'the string is {x}', args=['name.first']),
                           'i': FunctionCall(func=operator.add, args=['i', 'j'])
                        }
                        Serializer(foo, mapper=mapper)


    """
    source = Structure
    mapper = Map[String, OneOf[String, FunctionCall]]

    def __validate__(self):
        source_class = self.source.__class__
        valid_keys = set(get_all_fields_by_name(source_class).keys())
        for key in self.mapper:
            if key not in valid_keys:
                raise ValueError("Invalid key in mapper for class {}: {}. Keys must be one of the class fields.".format(
                    source_class.__name__, key))
            if isinstance(self.mapper[key], (FunctionCall,)):
                args = self.mapper[key].args
                if isinstance(args, (list,)):
                    for arg in args:
                        if arg not in valid_keys:
                            raise ValueError(
                                "Mapper[{}] has a function call with an invalid argument: {}".format(key, arg))

    def serialize(self, compact=True):
        return serialize(self.source,
                         mapper=self.mapper,
                         compact=compact)
