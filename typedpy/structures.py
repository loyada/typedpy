"""
The Skeleton classes to support strictly defined structures:
Structure, Field, StructureReference, ClassReference, TypedField
"""
import enum
import json
from copy import deepcopy
from collections import OrderedDict, deque, defaultdict
from inspect import Signature, Parameter, signature
import sys
import typing
import hashlib

from typing import get_type_hints, Iterable

from .commons import wrap_val, _is_sunder, _is_dunder
from .utility import type_is_generic

REQUIRED_FIELDS = "_required"
DEFAULTS = "_defaults"
ADDITIONAL_PROPERTIES = "_additionalProperties"
IS_IMMUTABLE = "_immutable"
OPTIONAL_FIELDS = "_optional"
MUST_BE_UNIQUE = "_must_be_unique"
IGNORE_NONE_VALUES = "_ignore_none"
MAPPER = "_serialization_mapper"
SPECIAL_ATTRIBUTES = {
    REQUIRED_FIELDS,
    ADDITIONAL_PROPERTIES,
    IS_IMMUTABLE,
    DEFAULTS,
    OPTIONAL_FIELDS,
    MAPPER,
    IGNORE_NONE_VALUES,
}

MAX_NUMBER_OF_INSTANCES_TO_VERIFY_UNIQUENESS = 100000

T = typing.TypeVar("T")


class ImmutableMixin:
    """
    Helper for making a field immutable
    """

    _field_definition = None
    _instance = None

    def _get_defensive_copy_if_needed(self, value):
        return deepcopy(value) if self._is_immutable() else value

    def _is_immutable(self):
        if getattr(self._field_definition, "_immutable", False):
            return True
        instance = getattr(self, "_instance", None)
        return getattr(self._instance, IS_IMMUTABLE, False) if instance else False

    def _raise_if_immutable(self):
        if self._is_immutable():
            name = getattr(self, "_name", None)
            raise ValueError("{}: Field is immutable".format(name))


def make_signature(
    names, required, additional_properties, bases_params_by_name, bases_required
):
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
            if (name in required or name in bases_required)
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
            if (name not in required and name not in bases_required)
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
    base_structures = (
        [
            base
            for base in bases
            if issubclass(base, Structure) and base is not Structure
        ]
        if "Structure" in globals()
        else []
    )
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


def _check_for_final_violations(classes):
    def is_sub_class(c, base):
        return issubclass(c, base) and c != base

    current_class, *inherited_class = classes
    for i, c in enumerate(inherited_class):
        if "FinalStructure" in globals() and isinstance(c, StructMeta):
            if "FinalStructure" in globals() and is_sub_class(c, FinalStructure):
                raise TypeError(
                    "Tried to extend {}, which is a FinalStructure. This is forbidden".format(
                        c.__name__
                    )
                )
            if "ImmutableStructure" in globals() and is_sub_class(
                c, ImmutableStructure
            ):
                raise TypeError(
                    "Tried to extend {}, which is an ImmutableStructure. This is forbidden".format(
                        c.__name__
                    )
                )

        if "_FieldMeta" in globals() and isinstance(c, _FieldMeta):
            if "ImmutableField" in globals() and is_sub_class(c, ImmutableField):
                raise TypeError(
                    "Tried to extend {}, which is an ImmutableField. This is forbidden".format(
                        c.__name__
                    )
                )


class _FieldMeta(type):
    _registry = {}

    def __new__(cls, name, bases, cls_dict):
        clsobj = super().__new__(cls, name, bases, dict(cls_dict))
        _check_for_final_violations(clsobj.mro())
        return clsobj

    def __getitem__(cls, val):
        if isinstance(val, Field):
            return val
        elif Field in getattr(val, "__mro__", {}):
            return val()
        elif Structure in getattr(val, "__mro__", {}):
            return ClassReference(val)
        elif is_function_returning_field(val):
            return val()
        elif val is None:
            return NoneField()
        else:

            def get_state(value):
                raise TypeError(
                    "pickling of implicit wrappers for non-Typedpy fields are unsupported"
                )

            if not isinstance(val, type):
                raise TypeError(
                    "Unsupported field type in definition: {}".format(wrap_val(val))
                )
            the_class = val.__name__
            if the_class in _FieldMeta._registry:
                return _FieldMeta._registry[the_class]
            short_hash = hashlib.sha256(the_class.encode("utf-8")).hexdigest()[:8]
            new_name = "Field_{}_{}".format(the_class, short_hash)
            class_as_field = create_typed_field(new_name, val)
            class_as_field.__getstate__ = get_state
            _FieldMeta._registry[the_class] = class_as_field
            return class_as_field()


class UniqueMixin:
    def defined_as_unique(self):
        return getattr(self, MUST_BE_UNIQUE, False)

    def __manage_uniqueness__(self):
        myclass = self.__class__
        if (
            getattr(myclass, MUST_BE_UNIQUE, False)
            and len(getattr(myclass, "_ALL_INSTANCES", set()))
            < MAX_NUMBER_OF_INSTANCES_TO_VERIFY_UNIQUENESS
        ):
            hash_of_instance = self.__hash__()
            if hash_of_instance in getattr(myclass, "_ALL_INSTANCES", set()):
                classname = self.__class__.__name__
                raise ValueError(
                    "Instance copy in {}, which is defined as unique. Instance is {}".format(
                        classname, self
                    )
                )
            getattr(myclass, "_ALL_INSTANCES", set()).add(hash_of_instance)

    def __manage_uniqueness_for_field__(self, instance, value):
        if not getattr(instance, "_instantiated", False):
            return
        field_name = getattr(self, "_name")
        structure_class_name = instance.__class__.__name__
        all_instances_by_struct_name = getattr(
            self, "_ALL_INSTANCES", defaultdict(dict)
        )
        instance_by_value_for_current_struct = all_instances_by_struct_name[
            structure_class_name
        ]
        if (
            getattr(self, MUST_BE_UNIQUE, False)
            and len(instance_by_value_for_current_struct)
            < MAX_NUMBER_OF_INSTANCES_TO_VERIFY_UNIQUENESS
        ):
            hash_of_field_val = value.__hash__()
            if (
                instance_by_value_for_current_struct.get(hash_of_field_val, instance)
                != instance
            ):
                raise ValueError(
                    "Instance copy of field {} in {}, which is defined as unique. "
                    "Instance is {}".format(
                        field_name, structure_class_name, wrap_val(value)
                    )
                )
            if hash_of_field_val not in instance_by_value_for_current_struct:
                instance_by_value_for_current_struct[hash_of_field_val] = instance


class Field(UniqueMixin, metaclass=_FieldMeta):
    """
    Base class for a field(i.e. property) in a structure.
    Should not be used directly by developers.
    Arguments:
        immutable: optional
            Marks the field as immutable. Typically the developer does not need to use it,
            as there is a high level API for making a field immutable

        is_unique: optional
            Marks a field as unique within this its Structure.
            as there is a high level API for making a field immutable

            .. code-block:: python

                    class SSID(String): pass

                    class Person(Structure):
                            ssid: SSID(is_unique=True)
                            name: String

                    Person(ssid="1234", name="john")
                    # the next line will raise an exception "Instance copy of field ssid in Person"
                    Person(ssid="1234", name="jeff")

            Alternatively, you can use the "@unique" decorator on the class definition of the Field.
            Refer to "Uniqueness" section for more detail.

        default: optional
            default value in case no value was assigned. Setting it makes
            the field implicitly optional.
            Default values are validated based on the field definition like any other value
            assignment.
    """

    def __init__(self, name=None, immutable=None, is_unique=None, default=None):
        self._name = name
        self._default = default
        if is_unique in [True, False]:
            setattr(self, MUST_BE_UNIQUE, is_unique)
            if is_unique:
                self._ALL_INSTANCES = defaultdict(dict)
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
        def get_field_with_inheritance(name):
            if name in owner.__dict__:
                return owner.__dict__[name]
            field_by_name = owner.get_all_fields_by_name()
            return field_by_name[name]

        if instance is not None and self._name not in instance.__dict__:
            return self._default
        res = (
            instance.__dict__[self._name]
            if instance is not None
            else get_field_with_inheritance(self._name)
        )
        is_immutable = (
            instance is not None
            and getattr(instance, IS_IMMUTABLE, False)
            or getattr(self, IS_IMMUTABLE, False)
        )
        needs_defensive_copy = (
            not isinstance(res, (ImmutableMixin, int, float, str, bool, enum.Enum))
            or res is None
        )
        return deepcopy(res) if (is_immutable and needs_defensive_copy) else res

    def __set__(self, instance, value):
        if getattr(self, IS_IMMUTABLE, False) and self._name in instance.__dict__:
            raise ValueError("{}: Field is immutable".format(self._name))
        if getattr(self, IS_IMMUTABLE, False) and not getattr(
            self, "_custom_deep_copy_implementation", False
        ):
            try:
                instance.__dict__[self._name] = deepcopy(value)
            except TypeError:
                raise TypeError(
                    "{} cannot be immutable, as its type does not support pickle.".format(
                        self._name
                    )
                )
        else:
            self.__manage_uniqueness_for_field__(instance, value)
            instance.__dict__[self._name] = value
            instance.__manage__uniqueness_of_all_fields__()
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

    def _set_immutable(self, immutable: bool):
        self._immutable = immutable


# noinspection PyBroadException
def is_function_returning_field(field_definition_candidate):
    python_ver_higher_than_36 = sys.version_info[0:2] != (3, 6)
    if callable(field_definition_candidate) and python_ver_higher_than_36:
        try:
            if len(signature(field_definition_candidate).parameters) > 0:
                raise TypeError("function not allowed to accept any parameters")
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
        if issubclass(the_class, Structure):
            field_names = getattr(the_class, "_fields", [])
            field_by_name = dict([(k, getattr(the_class, k)) for k in field_names])
            all_fields_by_name.update(field_by_name)
    return all_fields_by_name


def _instantiate_fields_if_needed(cls_dict: dict, defaults: dict):
    for key, val in cls_dict.items():
        if (
            key not in SPECIAL_ATTRIBUTES
            and not isinstance(val, Field)
            and not key.startswith("__")
            and (
                Field in getattr(val, "__mro__", []) or is_function_returning_field(val)
            )
        ):
            new_val = val(default=defaults[key]) if key in defaults else val()
            cls_dict[key] = new_val


def _apply_default_and_update_required_not_to_include_fields_with_defaults(
    cls_dict: dict, defaults: dict, fields: list
):
    required_fields = set(cls_dict.get(REQUIRED_FIELDS, []))
    optional_fields = set(cls_dict.get(OPTIONAL_FIELDS, []))
    required_fields_predefined = REQUIRED_FIELDS in cls_dict
    for field_name in fields:
        if field_name in defaults and not getattr(
            cls_dict[field_name], "_default", None
        ):
            cls_dict[field_name]._try_default_value(defaults[field_name])
            cls_dict[field_name]._default = defaults[field_name]
        if getattr(cls_dict[field_name], "_default", None) is not None:
            if field_name in required_fields:
                required_fields.remove(field_name)
        elif not required_fields_predefined:
            if field_name not in optional_fields:
                required_fields.add(field_name)
    cls_dict[REQUIRED_FIELDS] = list(required_fields)


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
        _check_for_final_violations(clsobj.mro())

        clsobj._fields = fields
        default_required = (
            list(set(bases_required + fields)) if bases_params else fields
        )
        required = cls_dict.get(REQUIRED_FIELDS, default_required)
        setattr(clsobj, REQUIRED_FIELDS, list(set(bases_required + required)))
        additional_props = cls_dict.get(ADDITIONAL_PROPERTIES, True)
        sig = make_signature(
            clsobj._fields,
            required,
            additional_props,
            bases_params,
            bases_required=bases_required,
        )
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
        Anything,
        Deque,
    )

    type_mapping = {
        deque: Deque,
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
        typing.Any: Anything,
    }
    return type_mapping.get(v, None)


def get_typing_lib_info(v):
    from .fields import AnyOf

    if v == type(None):
        return NoneField()

    if not type_is_generic(v):
        return convert_basic_types(v)
    origin = getattr(v, "__origin__", None)
    mapped_type = convert_basic_types(origin)
    if mapped_type is None:
        raise TypeError("{} type is not supported".format(v))
    args_raw = getattr(v, "__args__", None)
    if not args_raw:
        return mapped_type()
    mapped_args = [
        get_typing_lib_info(a) for a in args_raw if not isinstance(a, typing.TypeVar)
    ]
    if not all(mapped_args):
        if mapped_type == AnyOf:
            for i, arg in enumerate(mapped_args):
                if arg is None:
                    if isinstance(args_raw[i], type):
                        mapped_args[i] = Field[args_raw[i]]
                    else:
                        raise TypeError("invalid type {}".format(v))
        else:
            raise TypeError("invalid type {}".format(v))
    if mapped_args:
        if mapped_type == AnyOf:
            return mapped_type(fields=mapped_args)
        else:
            mapped_args = mapped_args if len(mapped_args) > 1 else mapped_args[0]
            return mapped_type(items=mapped_args)
    return mapped_type()


def add_annotations_to_class_dict(cls_dict):
    annotations = cls_dict.get("__annotations__", {})
    defaults = {}
    optional_fields = set(cls_dict.get(OPTIONAL_FIELDS, []))
    if isinstance(annotations, dict):
        for k, v in annotations.items():
            first_arg = getattr(v, "__args__", [0])[0]
            mros = getattr(first_arg, "__mro__", getattr(v, "__mro__", []))
            if not type_is_generic(v) and (
                isinstance(v, (Field, Structure)) or Field in mros or Structure in mros
            ):
                if k in cls_dict:
                    defaults[k] = cls_dict[k]
                cls_dict[k] = v
            else:
                the_type = get_typing_lib_info(v)
                if the_type:
                    from .fields import AnyOf

                    if isinstance(the_type, AnyOf) and getattr(
                        the_type, "_is_optional", False
                    ):
                        optional_fields.add(k)
                    if k in cls_dict:
                        default = cls_dict[k]
                        try:
                            if isinstance(the_type, Field):
                                the_type._try_default_value(default)
                            else:
                                the_type = the_type(default=default)
                        except Exception as e:
                            raise e.__class__("{}: {}".format(k, str(e))) from e
                        defaults[k] = cls_dict[k]
                    cls_dict[k] = the_type
    if optional_fields:
        cls_dict[OPTIONAL_FIELDS] = optional_fields
    cls_dict[DEFAULTS] = defaults


class Structure(UniqueMixin, metaclass=StructMeta):
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

        _optional: optional
            If we don't state the "_required" field, we can state which fields are optional instead.
            Example:

            .. code-block:: python

                class Foo(Structure):
                    id = Integer
                    name = String
                    _optional = ['name']


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

        _ignore_none(bool): optional
             Ignore assignment to None for any field value.
             Default is False.
             Required fields never ignore None (since they are required)

    Decorating it with @unique ensures that no all instances of this structure will be unique. It
    will raise an exception otherwise (see "Uniqueness" section).
    """

    _fields = []
    _fail_fast = True

    def __init__(self, *args, **kwargs):
        bound = getattr(self, "__signature__").bind(*args, **kwargs)
        if "kwargs" in bound.arguments:
            for name, val in bound.arguments["kwargs"].items():
                setattr(self, name, val)
            del bound.arguments["kwargs"]

        if Structure.failing_fast():
            for name, val in bound.arguments.items():
                setattr(self, name, val)
        else:
            errors = []
            for name, val in bound.arguments.items():
                try:
                    setattr(self, name, val)
                except (TypeError, ValueError) as ex:
                    errors.append(ex)
            if errors:
                messages = json.dumps([str(e) for e in errors])
                raise errors[0].__class__(messages) from errors[0]

        self.__validate__()
        self._instantiated = True
        self.__manage_uniqueness__()
        self.__manage__uniqueness_of_all_fields__()

    def __manage__uniqueness_of_all_fields__(self):
        fields_by_name = _get_all_fields_by_name(self.__class__)
        for name, field in fields_by_name.items():
            if field.defined_as_unique():
                field.__manage_uniqueness_for_field__(self, getattr(self, name, None))

    def __setattr__(self, key, value):
        if getattr(self, IS_IMMUTABLE, False):
            if key in self.__dict__:
                raise ValueError("Structure is immutable")
            value = deepcopy(value)
        if all(
            [
                getattr(self, IGNORE_NONE_VALUES, False),
                value is None,
                key not in getattr(self.__class__, REQUIRED_FIELDS, []),
            ]
        ):
            return

        super().__setattr__(key, value)

        if (
            getattr(self, "_instantiated", False)
            and not _is_dunder(key)
            and not _is_sunder(key)
        ):
            self.__manage_uniqueness__()

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

    def __repr__(self):
        return self.__str__()

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
        if isinstance(getattr(self, REQUIRED_FIELDS), list) and key in getattr(
            self, REQUIRED_FIELDS
        ):
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

    def _is_wrapper(self):
        field_by_name = _get_all_fields_by_name(self.__class__)
        field_names = list(field_by_name.keys())
        props = self.__class__.__dict__
        required = props.get(REQUIRED_FIELDS, field_names)
        additional_props = props.get(ADDITIONAL_PROPERTIES, True)
        return (
            len(field_names) == 1
            and required == field_names
            and additional_props is False
        )

    def __contains__(self, item):
        if self._is_wrapper():
            field_by_name = _get_all_fields_by_name(self.__class__)
            field_names = list(field_by_name.keys())
            return item in getattr(self, field_names[0], {})

        raise TypeError(
            "{} does not support this operator".format(self.__class__.__name__)
        )

    def __iter__(self):
        field_by_name = _get_all_fields_by_name(self.__class__)
        field_names = list(field_by_name.keys())
        val = getattr(self, field_names[0], {})

        if self._is_wrapper() and hasattr(val, "__iter__"):
            return iter(val)
        raise TypeError(
            "{} is not a wrapper of an iterable".format(self.__class__.__name__)
        )

    def shallow_clone_with_overrides(self, **kw):
        fields_names = self.get_all_fields_by_name().keys()
        field_value_by_name = dict(
            [
                (f, getattr(self, f))
                for f in fields_names
                if getattr(self, f) is not None
            ]
        )
        kw_args = {**field_value_by_name, **kw}
        return self.__class__(**kw_args)

    def cast_to(self, cls: type(T)) -> T:
        """
        Shallow copy of the structure as the given class, which should be a subclass
        or superclass of the structure's class
        :param cls: the target class
        :return: an instance of cls
        """
        if (
            issubclass(cls, self.__class__)
            or cls is self.__class__
            or isinstance(self, cls)
        ) and issubclass(cls, Structure):
            that = (
                deepcopy(self)
                if (
                    issubclass(cls, ImmutableStructure)
                    or issubclass(self.__class__, ImmutableStructure)
                )
                else self
            )

            fields_names = cls.get_all_fields_by_name().keys()
            field_value_by_name = dict(
                [
                    (f, getattr(that, f))
                    for f in fields_names
                    if getattr(that, f, None) is not None
                ]
            )
            return cls(**field_value_by_name)

        raise TypeError(f"cls must be subclass of {self.__class__.__name__}")

    @staticmethod
    def set_fail_fast(fast_fail: bool):
        Structure._fail_fast = fast_fail

    @staticmethod
    def failing_fast():
        return Structure._fail_fast


class FinalStructure(Structure):
    pass


def unique(cls):
    if issubclass(cls, Structure):
        setattr(cls, MUST_BE_UNIQUE, True)
        cls._ALL_INSTANCES = set()
    elif issubclass(cls, Field):
        setattr(cls, MUST_BE_UNIQUE, True)
        cls._ALL_INSTANCES = defaultdict(dict)
    return cls


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

        # any of the following lines will raise an exception:
        b.y = 1
        b.z[1] += 1
        b.m['c'] = 4
        b.z.clear()
        b.m.pop('a')

    ImmutableStructure class (as the class B in the example above) are not allowed to be extended.
    This is to ensure any instance of ImmutableStructure is indeed immutable.
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

        if not isinstance(value, self._ty) and value is not None:
            raise TypeError(
                "{}Expected {}; Got {}".format(err_prefix(), self._ty, wrap_val(value))
            )

    def __set__(self, instance, value):
        if not getattr(instance, "_skip_validation", False):
            self._validate(value)
        super().__set__(instance, value)


class NoneField(TypedField):
    """
    A field that maps to a single allowable value: None.
    By default, fields cannot be assigned None (i.e. "Null Safety"). NoneField allows to do so.
    This is useful to define optional fields or optional values such as:

    .. code-block:: python

       class Foo(Structure):
           optional_1: typing.Optional[Array]     # NoneField is used implicitly
           optional_2: AnyOf[Array, NoneField]
           optional_3: AnyOf[Array, None]         # the conversion from None to NoneField is implicit

           arr_maybe_int_1: Array[AnyOf[Integer, NoneField]]
           arr_maybe_int_2: Array[AnyOf[Integer, None]]    # the conversion from None to NoneField is implicit

    """

    _ty = type(None)


class ValidatedTypedField(TypedField):
    def __set__(self, instance, value):
        self._validate_func(value)  # pylint: disable=E1101
        super().__set__(instance, value)


def create_typed_field(classname, cls, validate_func=None):
    """
    Factory that generates a new class for a :class:`Field` as a wrapper of any class.
    Example:
    Given a class Foo, and a validation function for the value in Foo - validate_foo, the line

    .. code-block:: python

        ValidatedFooField = create_typed_field("FooField", Foo, validate_func=validate_foo)

    Generates a new :class:`Field` class that validates the content using validate_foo, and can be
    used just like any :class:`Field` type.

    .. code-block:: python

        class A(Structure):
            foo = ValidatedFooField
            bar = Integer

        # asumming we have an instance of Foo, called my_foo:
        A(bar=4, foo=my_foo)

    Arguments:

        classname(`str`):
            the content must not match any of the fields in the lists
    """

    def validate_wrapper(cls, value):
        if validate_func is None:
            return
        validate_func(value)

    return type(
        classname,
        (ValidatedTypedField,),
        {"_validate_func": validate_wrapper, "_ty": cls},
    )


class ClassReference(TypedField):
    """
    A field that is a reference to another Structure instance.
    """

    def __init__(self, cls):
        self._ty = cls
        super().__init__(cls)

    def __str__(self):
        return "<ClassReference: {}>".format(self._ty.__name__)


class ImmutableField(Field):
    """
    A mixin that makes a field class immutable.
    For Example:

     .. code-block:: python

         class MyFieldType(Field): .....

         class MyImmutableFieldType(ImmutableField, MyFieldType): pass

         # that's all you have to do to make MyImmutableFieldType immutable.

    ImmutableField class (as the class MyImmutableFieldType in the example above) are
    not allowed to be extended. This is to ensure any instance of
    ImmutableField is indeed immutable.
    """

    _immutable = True
