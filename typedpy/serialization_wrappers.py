from typedpy import Structure
from typedpy.fields import StructureClass, Map, String, OneOf, Boolean
from typedpy.serialization import FunctionCall, deserialize_structure, serialize
from typedpy.structures import _get_all_fields_by_name


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
                Deserializer(target_class=Foo, mapper = mapper).deserializer(the_input_dict)

        camel_case_convert(bool): Optional
            If true, will convert any camelCase key that does not have explicit mapping to a snake_case attribute
            name. Default is False.

    """

    target_class = StructureClass
    mapper = Map[String, OneOf[String, FunctionCall, Map]]
    camel_case_convert = Boolean(default = False)

    _required = ["target_class"]

    def __validate__(self):
        valid_keys = set(_get_all_fields_by_name(self.target_class).keys())
        if self.mapper:
            for key in self.mapper:
                if key.split(".")[0] not in valid_keys:
                    raise ValueError(
                        "Invalid key in mapper for class {}: {}. Keys must be one of the class fields.".format(
                            self.target_class.__name__, key
                        )
                    )

    def deserialize(self, input_data, keep_undefined=True):
        return deserialize_structure(
            self.target_class,
            input_data,
            mapper=self.mapper,
            keep_undefined=keep_undefined,
            camel_case_convert=self.camel_case_convert,
        )


class Serializer(Structure):
    """
           A high level API for a serializer: from an instance of :class:`Structure`, to something that can be sent as a Json
           (usually a dict). The advantage of this over the lower level function is that it is more explicit and
           self-validating. In other words, it prevents the user from creating an invalid mapper.

           Arguments:
               source(:class:`Structure`):
                   An instance of :class:`Structure` that this serializer is build for.
                   Example:

                   .. code-block:: python

                       class Foo(Structure):
                           i = Integer
                           f = Float

                       foo = Foo(f=5.5, i=999)
                       Serializer(source=foo)


               mapper(dict): optional
                   The key is the target key name. The value can either be a path of the value in the source object
                   using dot notation, for example: "aaa.bbb", or a :class:`FunctionCall`. In the latter case,
                   the function is the used to preprocess the input prior to deserialization/validation. \
                   The args attribute in the function call is optional. If non provided, the input to the function is
                   the attribute with the same key. Otherwise it is the names of the attributes  in the input that are injected
                   to the provided function. \
                   See working examples in the tests link above. \
                   This class will ensure that the mapper is a valid one for its target_class.
                   Example:

                   .. code-block:: python

                        class Foo(Structure):
                            f = Float
                            i = Integer

                        foo = Foo(f=5.5, i=999)
                        mapper = {
                            'output_floats': FunctionCall(func=lambda f: [int(f)], args=['i']),
                            'output_int': FunctionCall(func=lambda x: str(x), args=['f'])
                        }
                        assert Serializer(source=foo, mapper=mapper).serialize() == {'output_floats': [999], 'output_int': '5.5'}


    """

    source = Structure
    mapper = Map[String, OneOf[String, FunctionCall, Map]]

    _required = ["source"]

    def __validate__(self):
        def verify_key_in_mapper(key, valid_keys, source_class):
            if key.split(".")[0] not in valid_keys:
                raise ValueError(
                    "Invalid key in mapper for class {}: {}. Keys must be one of the class fields.".format(
                        source_class.__name__, key
                    )
                )
            if isinstance(self.mapper[key], (FunctionCall,)):
                args = self.mapper[key].args
                if isinstance(args, (list,)):
                    for arg in args:
                        if arg not in valid_keys:
                            raise ValueError(
                                "Mapper[{}] has a function call with an invalid argument: {}".format(
                                    key, arg
                                )
                            )

        source_class = self.source.__class__
        valid_keys = set(_get_all_fields_by_name(source_class).keys())
        if self.mapper:
            for key in self.mapper:
                verify_key_in_mapper(key, valid_keys, source_class)

    def serialize(self, compact: bool = True, camel_case_convert: bool = False):
        """

        Arguments:
              compact(boolean): optional
                    whether to use a compact form for Structure that is a simple wrapper of a field.
                    for example: if a Structure has only one field of an int, if compact is True
                    it will serialize the structure as an int instead of a dictionary.
                    Default is False.

              camel_case_convert(dict): optional
                    If True, convert any camel-case key that does not have a mapping in the mapper to a snake-case
                    attribute.
                    Default is False.
        """
        return serialize(
            self.source,
            mapper=self.mapper,
            compact=compact,
            camel_case_convert=camel_case_convert,
        )
