"""
The Skeleton classes to support strictly defined structures:
Structure, Field, StructureReference, ClassReference, TypedField
"""
from copy import deepcopy
from collections import OrderedDict
from inspect import Signature, Parameter
import sys
import typing

from typing import get_type_hints, Iterable

from typedpy.commons import wrap_val

REQUIRED = "_required"
DEFAULTS = "_defaults"
ADDITIONAL_PROPERTIES = "_additionalProperties"
IS_IMMUTABLE = "_immutable"


def make_signature(names, required, additional_properties, bases_params_by_name):
    """
    Make a signature that will be used for the constructor of the Structure
    :param names: names of the properties
    :param required: list of required properties
    :param additional_properties: are additional properties allowed?
    :param bases_params_by_name: parameters taken from base classes (i.e. MRO)
           in case of inheritance
    :return: the signature
    """

    non_default_args_for_class = OrderedDict(
        [
            (name, Parameter(name, Parameter.POSITIONAL_OR_KEYWORD))
            for name in names
            if name in required
        ]
    )
    non_default_args_for_bases = OrderedDict(
        [
            (name, param)
            for (name, param) in bases_params_by_name.items()
            if name in required
        ]
    )
    non_default_args = list(
        {**non_default_args_for_bases, **non_default_args_for_class}.values()
    )

    default_args_for_class = OrderedDict(
        [
            (name, Parameter(name, Parameter.POSITIONAL_OR_KEYWORD, default=None))
            for name in names
            if name not in required
        ]
    )
    default_args_for_bases = OrderedDict(
        [
            (name, param)
            for (name, param) in bases_params_by_name.items()
            if name not in required
        ]
    )
    default_args = list({**default_args_for_bases, **default_args_for_class}.values())

    additional_args = (
        [Parameter("kwargs", Parameter.VAR_KEYWORD)] if additional_properties else []
    )

    return Signature(non_default_args + default_args + additional_args)


def get_base_info(bases):
    """
    Extract the parameters from all the base classes to support inheritance of Structures.
    :param bases: list of base classes
    :return:  a tuple of: (the parameters from the base classes, a list of the names of
              the required ones)
    """
    bases_params = OrderedDict()
    bases_required = []
    base_structures = [
        base for base in bases if issubclass(base, Structure) and base is not Structure
    ]
    for base in base_structures:
        for k, param in getattr(base, "__signature__").parameters.items():
            if k not in bases_params:
                if param.default is not None and param.kind != Parameter.VAR_KEYWORD:
                    bases_required.append(k)
                bases_params[k] = param
        additional_props = base.__dict__.get(ADDITIONAL_PROPERTIES, True)
        if additional_props and bases_params["kwargs"].kind == Parameter.VAR_KEYWORD:
            del bases_params["kwargs"]

    return bases_params, bases_required


class Field:
    """
    Base class for a field(i.e. property) in a structure.
    Should not be used directly by developers.
    """

    def __init__(self, name=None, immutable=None, default=None):
        self._name = name
        self._default = default
        if immutable is not None:
            self._immutable = immutable
        if default:
            self._try_default_value(default)

    def _try_default_value(self, default):
        try:
            self.__set__(Structure(), default)
        except Exception as e:
            raise e.__class__(
                "Invalid default value: {}; Reason: {}".format(
                    wrap_val(default), str(e)
                )
            ) from e

    def __get__(self, instance, owner):
        if instance is not None and self._name not in instance.__dict__:
            return self._default
        return (
            instance.__dict__[self._name]
            if instance is not None
            else owner.__dict__[self._name]
        )

    def __set__(self, instance, value):
        if getattr(self, IS_IMMUTABLE, False) and self._name in instance.__dict__:
            raise ValueError("{}: Field is immutable".format(self._name))
        if getattr(self, IS_IMMUTABLE, False) and not getattr(
            self, "_custom_deep_copy_implementation", False
        ):
            instance.__dict__[self._name] = deepcopy(value)
        else:
            instance.__dict__[self._name] = value
        if getattr(instance, "_instantiated", False) and not getattr(
            instance, "_skip_validation", False
        ):
            instance.__validate__()

    def __serialize__(self, value):  # pylint: disable=R0201
        return value

    def __str__(self):
        def as_str(the_val):
            """
            convert to string or a list of strings
            :param the_val: a Field or a list of Fields
            :return: a string representation
            """
            if hasattr(the_val, "__iter__"):
                return "[{}]".format(", ".join([str(v) for v in the_val]))
            return str(the_val)

        name = self.__class__.__name__
        props = []
        for k, val in sorted(self.__dict__.items()):
            if val is not None and not k.startswith("_"):
                strv = "'{}'".format(val) if isinstance(val, str) else as_str(val)
                props.append("{} = {}".format(k, strv))

        propst = ". Properties: {}".format(", ".join(props)) if props else ""
        return "<{}{}>".format(name, propst)


# noinspection PyBroadException
def is_function_returning_field(field_definition_candidate):
    python_ver_higher_than_36 = sys.version_info[0:2] != (3, 6)
    if callable(field_definition_candidate) and python_ver_higher_than_36:
        try:
            return_value = get_type_hints(field_definition_candidate).get(
                "return", None
            )
            return return_value == Field or Field in getattr(
                return_value.__args__[0], "__mro__", []
            )
        except Exception:
            return False
    return False


def _get_all_fields_by_name(cls):
    all_classes = reversed([c for c in cls.mro() if isinstance(c, StructMeta)])
    all_fields_by_name = {}
    for the_class in all_classes:
        field_by_name = {
            k: v for k, v in the_class.__dict__.items() if isinstance(v, Field)
        }
        all_fields_by_name.update(field_by_name)
    return all_fields_by_name


def _instantiate_fields_if_needed(cls_dict: dict, defaults: dict):
    for key, val in cls_dict.items():
        if (
            key not in {REQUIRED, ADDITIONAL_PROPERTIES, IS_IMMUTABLE, DEFAULTS}
            and not isinstance(val, Field)
            and (
                Field in getattr(val, "__mro__", []) or is_function_returning_field(val)
            )
        ):
            new_val = val(default=defaults[key]) if key in defaults else val()
            cls_dict[key] = new_val


def _apply_default_and_update_required_not_to_include_fields_with_defaults(
    cls_dict: dict, defaults: dict, fields: list
):
    required_fields = set(cls_dict.get(REQUIRED, []))
    required_fields_predefined = REQUIRED in cls_dict
    for field_name in fields:
        if field_name in defaults and not getattr(
            cls_dict[field_name], "_default", None
        ):
            cls_dict[field_name]._try_default_value(defaults[field_name])
            cls_dict[field_name]._default = defaults[field_name]
        if getattr(cls_dict[field_name], "_default", None):
            if field_name in required_fields:
                required_fields.remove(field_name)
        elif not required_fields_predefined:
            required_fields.add(field_name)
    cls_dict[REQUIRED] = list(required_fields)


class StructMeta(type):
    """
    Metaclass for Structure. Manipulates it to ensure the fields are set up correctly.
    """

    @classmethod
    def __prepare__(cls, name, bases):
        return OrderedDict()

    def __new__(cls, name, bases, cls_dict):
        bases_params, bases_required = get_base_info(bases)
        add_annotations_to_class_dict(cls_dict)
        defaults = cls_dict[DEFAULTS]
        _instantiate_fields_if_needed(cls_dict=cls_dict, defaults=defaults)

        for key, val in cls_dict.items():
            if isinstance(val, StructMeta) and not isinstance(val, Field):
                cls_dict[key] = ClassReference(val)
        fields = [key for key, val in cls_dict.items() if isinstance(val, Field)]
        for field_name in fields:
            if field_name.startswith("_") or field_name == "kwargs":
                raise ValueError("{}: invalid field name".format(field_name))
            setattr(cls_dict[field_name], "_name", field_name)

        _apply_default_and_update_required_not_to_include_fields_with_defaults(
            cls_dict=cls_dict, defaults=defaults, fields=fields
        )

        cls_dict.pop(DEFAULTS, None)
        clsobj = super().__new__(cls, name, bases, dict(cls_dict))

        clsobj._fields = fields
        default_required = (
            list(set(bases_required + fields)) if bases_params else fields
        )
        required = cls_dict.get(REQUIRED, default_required)
        additional_props = cls_dict.get(ADDITIONAL_PROPERTIES, True)
        sig = make_signature(clsobj._fields, required, additional_props, bases_params)
        setattr(clsobj, "__signature__", sig)
        return clsobj

    def __str__(cls):
        name = cls.__name__
        props = []
        for k, val in sorted(cls.__dict__.items()):
            if val is not None and not k.startswith("_"):
                strv = "'{}'".format(val) if isinstance(val, str) else str(val)
                props.append("{} = {}".format(k, strv))
        return "<Structure: {}. Properties: {}>".format(name, ", ".join(props))


def convert_basic_types(v):
    from .fields import (
        Integer,
        Float,
        String,
        Map,
        Array,
        Tuple,
        Set,
        Boolean,
        ImmutableSet,
        AnyOf,
        Anything
    )

    type_mapping = {
        int: Integer,
        str: String,
        float: Float,
        dict: Map,
        set: Set,
        list: Array,
        tuple: Tuple,
        bool: Boolean,
        frozenset: ImmutableSet,
        typing.Union: AnyOf,
        typing.Any: Anything
    }
    return type_mapping.get(v, None)


def get_typing_lib_info(v):
    from .fields import AnyOf
    class Foo: pass

    py_version = sys.version_info[0:2]
    python_ver_atleast_than_37 = py_version >= (3, 6)
    python_ver_atleast_39 = py_version >= (3, 9)

    generic_alias = getattr(typing, "_GenericAlias", Foo)
    special_generic_alias = getattr(typing, "_SpecialGenericAlias", Foo)
    origin = getattr(v, "__origin__", None)
    is_typing_generic = (python_ver_atleast_than_37 and isinstance(v, (generic_alias, special_generic_alias))) or (
         python_ver_atleast_39 and origin in {list, dict, tuple, set, frozenset, typing.Union})
    if not is_typing_generic:
        return convert_basic_types(v)
    mapped_type = convert_basic_types(origin)
    args_raw = getattr(v, "__args__", None)
    if not args_raw:
        return mapped_type()
    mapped_args = [
        get_typing_lib_info(a) for a in args_raw if not isinstance(a, typing.TypeVar)
    ]
    if not all(mapped_args):
        raise TypeError("invalid type {}".format(v))
    if mapped_args:
        if mapped_type == AnyOf:
            return mapped_type(fields=mapped_args)
        else:
            mapped_args = mapped_args if len(mapped_args)>1 else mapped_args[0]
            return mapped_type(items=mapped_args)
    return mapped_type()


def add_annotations_to_class_dict(cls_dict):
    annotations = cls_dict.get("__annotations__", {})
    defaults = {}
    if isinstance(annotations, dict):
        for k, v in annotations.items():
            first_arg = getattr(v, "__args__", [0])[0]
            mros = getattr(first_arg, "__mro__", getattr(v, "__mro__", []))
            if isinstance(v, (Field, Structure)) or Field in mros or Structure in mros:
                if k in cls_dict:
                    defaults[k] = cls_dict[k]
                cls_dict[k] = v
            else:
                the_type = get_typing_lib_info(v)
                if the_type:
                    if k in cls_dict:
                        try:
                            the_type = the_type(default=cls_dict[k])
                        except Exception as e:
                            raise e.__class__("{}: {}".format(k, str(e))) from e
                        defaults[k] = cls_dict[k]
                    cls_dict[k] = the_type
    cls_dict[DEFAULTS] = defaults


class Structure(metaclass=StructMeta):
    """
    The base class to support strictly defined structures. When creating a new instance of
    a Structure, fields must be provided by name.
    Supports basic constructs: string conversion, quality, copy, deep-copy, hash etc.

    Arguments:
        _required: optional
            An array of the mandatory fields. The default is all the fields in the class.
            Example:

            .. code-block:: python

                class Foo(Structure):
                    _required = ['id']

                    id = Integer
                    name = String

                # this is valid:
                Foo(id = 1)

                # this raises an exception:
                Foo(name="John")

        _additionalProperties(bool): optional
            Is it allowed to add additional properties that are not defined in the class definition?
            the default is True.
            Example:

            .. code-block:: python

                class Foo(Structure):
                    _additionalProperties = False

                    id = Integer

                # this is valid:
                Foo(id = 1)

                # this raises an exception:
                Foo(id = 1, a = 2)

    """

    _fields = []

    def __init__(self, *args, **kwargs):
        bound = getattr(self, "__signature__").bind(*args, **kwargs)
        if "kwargs" in bound.arguments:
            for name, val in bound.arguments["kwargs"].items():
                setattr(self, name, val)
            del bound.arguments["kwargs"]
        for name, val in bound.arguments.items():
            setattr(self, name, val)

        self.__validate__()
        self._instantiated = True

    def __setattr__(self, key, value):
        if getattr(self, IS_IMMUTABLE, False):
            if key in self.__dict__:
                raise ValueError("Structure is immutable")
            value = deepcopy(value)
        super().__setattr__(key, value)

    def __getstate__(self):
        fields_by_name = _get_all_fields_by_name(self.__class__)
        return {
            name: field.__serialize__(getattr(self, name, None))
            for (name, field) in fields_by_name.items()
            if name in self.__dict__
        }

    def __str__(self):
        def list_to_str(values):
            as_strings = [to_str(v) for v in values]
            return ",".join(as_strings)

        def dict_to_str(values):
            as_strings = [
                "{} = {}".format(to_str(k), to_str(v)) for (k, v) in values.items()
            ]
            return ",".join(as_strings)

        def to_str(the_val):
            if isinstance(the_val, list):
                return "[{}]".format(list_to_str(the_val))
            if isinstance(the_val, tuple):
                return "({})".format(list_to_str(the_val))
            if isinstance(the_val, set):
                return "{{{}}}".format(list_to_str(the_val))
            if isinstance(the_val, dict):
                return "{{{}}}".format(dict_to_str(the_val))
            return str(the_val)

        name = self.__class__.__name__
        if name.startswith("StructureReference_") and self.__class__.__bases__ == (
            Structure,
        ):
            name = "Structure"
        props = []
        internal_props = ["_instantiated"]
        for k, val in sorted(self.__dict__.items()):
            if k not in internal_props:
                strv = "'{}'".format(val) if isinstance(val, str) else to_str(val)
                props.append("{} = {}".format(k, strv))
        return "<Instance of {}. Properties: {}>".format(name, ", ".join(props))

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        internal_props = ["_instantiated"]
        for k, val in sorted(self.__dict__.items()):
            if k not in internal_props and val != other.__dict__.get(k):
                return False
        for k, val in sorted(other.__dict__.items()):
            if k not in internal_props and val != self.__dict__.get(k):
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return str(self).__hash__()

    def __delitem__(self, key):
        if isinstance(getattr(self, REQUIRED), list) and key in getattr(self, REQUIRED):
            raise ValueError("{} is mandatory".format(key))
        del self.__dict__[key]

    def __validate__(self):
        pass

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        result._skip_validation = True
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        delattr(result, "_skip_validation")
        return result

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __dir__(self) -> Iterable[str]:
        internal_props = ["_instantiated"]
        return [k for k in sorted(self.__dict__) if k not in internal_props]

    def __bool__(self):
        internal_props = ["_instantiated"]
        return any(
            [v is not None for k, v in self.__dict__.items() if k not in internal_props]
        )

    @classmethod
    def get_all_fields_by_name(cls):
        return _get_all_fields_by_name(cls)

    def __contains__(self, item):
        field_by_name = _get_all_fields_by_name(self.__class__)
        field_names = list(field_by_name.keys())
        props = self.__class__.__dict__
        required = props.get(REQUIRED, field_names)
        additional_props = props.get(ADDITIONAL_PROPERTIES, True)
        if (
            len(field_names) == 1
            and required == field_names
            and additional_props is False
        ):
            return item in getattr(self, field_names[0], {})

        raise TypeError(
            "{} does not support this operator".format(self.__class__.__name__)
        )


class ImmutableStructure(Structure):
    """
    A base class for a structure in which non of the fields can be updated post-creation
    Example:

    .. code-block:: python

        class B(ImmutableStructure):
            _required = []
            y = Number
            z = Array[Number]
            m = Map[String, Number]

        b = B(y = 3, z = [1,2,3], m = {'a': 1, 'b': 2})

        # each of the following lines will raise an exception:
        b.y = 1
        b.z[1] += 1
        b.m['c'] = 4

    """

    _immutable = True


class TypedField(Field):
    """
    A strictly typed base field.
    Should not be used directly. Instead, use :func:`create_typed_field`
    """

    _ty = object

    def _validate(self, value):
        def err_prefix():
            return "{}: ".format(self._name) if self._name else ""

        if not isinstance(value, (self._ty)) and value is not None:
            raise TypeError(
                "{}Expected {}; Got {}".format(err_prefix(), self._ty, wrap_val(value))
            )

    def __set__(self, instance, value):
        if not getattr(instance, "_skip_validation", False):
            self._validate(value)
        super().__set__(instance, value)


class ClassReference(TypedField):
    """
    A field that is a reference to another Structure instance.
    """

    def __init__(self, cls):
        self._ty = cls
        super().__init__(cls)

    def __str__(self):
        return "<ClassReference: {}>".format(self._ty.__name__)
