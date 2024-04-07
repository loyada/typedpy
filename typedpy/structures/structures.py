# pylint: disable=too-many-lines
"""
The Skeleton classes to support strictly defined structures:
Structure, Field, StructureReference, ClassReference, TypedField
"""
import enum
import inspect
import json
from builtins import enumerate, issubclass
from copy import deepcopy
from collections import OrderedDict, defaultdict
from collections.abc import Mapping
from inspect import Signature, Parameter, signature, currentframe
import sys
import typing
import hashlib
from json import JSONDecodeError

from typing import get_type_hints, Iterable

from typedpy.commons import (
    Constant,
    Undefined,
    raise_errs_if_needed,
    wrap_val,
    _is_sunder,
    _is_dunder,
)
from typedpy.utility import type_is_generic
from .consts import (
    ADDITIONAL_PROPERTIES,
    CUSTOM_ATTRIBUTE_MARKER,
    DEFAULTS,
    DESERIALIZATION_MAPPER,
    DISABLE_PROTECTION,
    IGNORE_NONE_VALUES,
    IS_IMMUTABLE,
    MAX_NUMBER_OF_INSTANCES_TO_VERIFY_UNIQUENESS,
    MUST_BE_UNIQUE,
    OLD_ADDITIONAL_PROPERTIES,
    OPTIONAL_FIELDS,
    REQUIRED_FIELDS,
    SERIALIZATION_MAPPER,
    SPECIAL_ATTRIBUTES,
    ENABLE_UNDEFINED,
)
from .defaults import TypedPyDefaults
from .type_mapping import convert_basic_types

T = typing.TypeVar("T")

_immutable_types = (int, float, str, tuple, bool, enum.Enum)
_internal_props = ["_instantiated", "_none_fields", "_trust_supplied_values"]
created_fast_serializer = "_created_fast_serializer"
failed_to_create_fast_serializer = "_failed_serializer_creation"


class ImmutableMixin:
    """
    Helper for making a field immutable
    """

    _field_definition = None
    _instance = None

    def _get_defensive_copy_if_needed(self, value):
        return (
            deepcopy(value)
            if (
                    not isinstance(
                        value,
                        (
                            int,
                            float,
                            str,
                            tuple,
                            bool,
                            enum.Enum,
                            ImmutableMixin,
                            ImmutableStructure,
                        ),
                    )
                    and self._is_immutable()
            )
            else value
        )

    def _is_immutable(self):
        if getattr(self._field_definition, "_immutable", False):
            return True
        instance = getattr(self, "_instance", None)
        return (
            getattr(self._instance, IS_IMMUTABLE, False)
            if instance is not None
            else False
        )

    def _raise_if_immutable(self):
        if self._is_immutable():
            name = getattr(self, "_name", None)
            raise ValueError(f"{name}: Field is immutable")


def make_signature(
        names: Iterable[str],
        *,
        required: Iterable[str],
        additional_properties: bool,
        bases_params_by_name: dict,
        bases_required,
        constants,
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
    all_names = set(names) | set(bases_params_by_name.keys())
    all_except_consts = all_names - set(constants)
    non_default_args_for_class = OrderedDict(
        [
            (name, Parameter(name, Parameter.POSITIONAL_OR_KEYWORD))
            for name in all_except_consts
            if name in required
        ]
    )
    non_default_args_for_bases = OrderedDict(
        [
            (name, param)
            for (name, param) in bases_params_by_name.items()
            if (name in required or name in bases_required) and name not in constants
        ]
    )
    non_default_args = list(
        {**non_default_args_for_bases, **non_default_args_for_class}.values()
    )

    default_args_for_class = OrderedDict(
        [
            (name, Parameter(name, Parameter.POSITIONAL_OR_KEYWORD, default=None))
            for name in names
            if (name not in required and name not in constants)
        ]
    )
    default_args_for_bases = OrderedDict(
        [
            (name, param)
            for (name, param) in bases_params_by_name.items()
            if (
                name not in required
                and name not in bases_required
                and name not in constants
                and (additional_properties or param.kind != Parameter.VAR_KEYWORD)
        )
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
        additional_props_fallback = base.__dict__.get(
            OLD_ADDITIONAL_PROPERTIES, TypedPyDefaults.additional_properties_default
        )
        additional_props = base.__dict__.get(
            ADDITIONAL_PROPERTIES, additional_props_fallback
        )
        if additional_props and bases_params["kwargs"].kind == Parameter.VAR_KEYWORD:
            del bases_params["kwargs"]

    return bases_params, bases_required


def _check_for_final_violations(classes):
    def is_sub_class(c, base):
        return issubclass(c, base) and c != base

    _, *inherited_class = classes
    for c in inherited_class:
        if "FinalStructure" in globals() and isinstance(c, StructMeta):
            if "FinalStructure" in globals() and is_sub_class(c, FinalStructure):
                raise TypeError(
                    f"Tried to extend {c.__name__}, which is a FinalStructure. This is forbidden"
                )
            if "ImmutableStructure" in globals() and is_sub_class(
                    c, ImmutableStructure
            ):
                raise TypeError(
                    f"Tried to extend {c.__name__}, which is an ImmutableStructure. This is forbidden"
                )

        if "FieldMeta" in globals() and isinstance(c, FieldMeta):
            if "ImmutableField" in globals() and is_sub_class(c, ImmutableField):
                raise TypeError(
                    f"Tried to extend {c.__name__}, which is an ImmutableField. This is forbidden"
                )


def _or_fields(first, other):
    from typedpy.fields import AnyOf, Enum

    if isinstance(other, (Field, Structure, FieldMeta, StructMeta)):
        return AnyOf[first, other]
    if isinstance(other, (str, int, float, bool, list, set, dict, tuple)):
        return AnyOf[first, Enum(values=[other])]
    converted = convert_basic_types(other)
    if converted:
        return AnyOf[first, converted]
    raise TypeError(f"| is Supported only between field types; Got {first} and {other}")


class FieldMeta(type):
    _registry = {}

    def __new__(cls, name, bases, cls_dict):
        clsobj = super().__new__(cls, name, bases, dict(cls_dict))
        _check_for_final_violations(clsobj.mro())
        return clsobj

    def __or__(cls, other):
        return _or_fields(cls, other)

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
            try:
                converted = convert_field_type_if_possible(val)
                if converted is None:
                    raise TypeError
                return FieldMeta.__getitem__(cls, converted)
            except TypeError:

                def get_state(value):
                    raise TypeError(
                        "pickling of implicit wrappers for non-Typedpy fields are unsupported"
                    )

                if not isinstance(val, type):
                    raise TypeError(
                        f"Unsupported field type in definition: {wrap_val(val)}"
                    )
                the_class = val.__name__
                if the_class in FieldMeta._registry:
                    return FieldMeta._registry[the_class]
                short_hash = hashlib.sha256(the_class.encode("utf-8")).hexdigest()[:8]
                new_name = f"Field_{the_class}_{short_hash}"
                class_as_field = create_typed_field(new_name, val)
                class_as_field.__getstate__ = get_state
                FieldMeta._registry[the_class] = class_as_field
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
                    f"Instance copy in {classname}, which is defined as unique. Instance is {self}"
                )
            getattr(myclass, "_ALL_INSTANCES", set()).add(hash_of_instance)

    def __manage_uniqueness_for_field__(self, instance, value):
        if not getattr(instance, "_instantiated", False) or not getattr(
                self, MUST_BE_UNIQUE, False
        ):
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
                    f"Instance copy of field {field_name} in {structure_class_name}, which is defined as unique. "
                    f"Instance is {wrap_val(value)}"
                )
            if hash_of_field_val not in instance_by_value_for_current_struct:
                instance_by_value_for_current_struct[hash_of_field_val] = instance


class Field(UniqueMixin, metaclass=FieldMeta):
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
            default_val = default() if callable(default) else default
            self._try_default_value(default_val)

    def __or__(self, other):
        return _or_fields(self, other)

    def _try_default_value(self, default):
        try:
            self._name = self._name or "value"
            self.__set__(  # pylint: disable=unnecessary-dunder-call
                Structure(), default
            )
        except Exception as e:
            raise e.__class__(
                f"Invalid default value: {wrap_val(default)}; Reason: {str(e)}"
            ) from e

    def __get__(self, instance, owner):
        def get_field_with_inheritance(name):
            if name in owner.__dict__:
                return owner.__dict__[name]
            field_by_name = owner.get_all_fields_by_name()
            return field_by_name.get(name)

        if instance is not None and self._name not in instance.__dict__:
            default_value = (
                self._default()
                if callable(self._default)
                else self._default
                if not getattr(instance.__class__, ENABLE_UNDEFINED, False)
                   or self._name in getattr(instance, "_none_fields", [])
                else Undefined
            )
            return default_value
        res = (
            instance.__dict__[self._name]
            if instance is not None
            else get_field_with_inheritance(self._name)
        )
        if (
                getattr(owner, DISABLE_PROTECTION, False)
                or not TypedPyDefaults.defensive_copy_on_get
        ):
            return res
        is_immutable = (
            getattr(instance, IS_IMMUTABLE, False)
            if instance is not None
            else getattr(self, IS_IMMUTABLE, False)
        )
        needs_defensive_copy = (
                not isinstance(
                    res,
                    (
                        ImmutableMixin,
                        int,
                        float,
                        str,
                        bool,
                        enum.Enum,
                        Field,
                        ImmutableStructure,
                    ),
                )
                or res is None
        )
        return deepcopy(res) if (is_immutable and needs_defensive_copy) else res

    def __set__(self, instance, value):
        if getattr(self, IS_IMMUTABLE, False) and self._name in instance.__dict__:
            raise ValueError(f"{self._name}: Field is immutable")
        if getattr(instance, "_trust_supplied_values", False):
            instance.__dict__[self._name] = value
            return

        if getattr(self, IS_IMMUTABLE, False) and not getattr(
                self, "_custom_deep_copy_implementation", False
        ):
            needs_defensive_copy = (
                    not isinstance(
                        value,
                        (
                            ImmutableMixin,
                            int,
                            float,
                            str,
                            bool,
                            enum.Enum,
                            ImmutableStructure,
                        ),
                    )
                    or value is None
            )
            try:
                instance.__dict__[self._name] = (
                    deepcopy(value) if needs_defensive_copy else value
                )
            except TypeError:
                raise TypeError(
                    f"{self._name} cannot be immutable, as its type does not support pickle."
                )
        else:
            if TypedPyDefaults.uniqueness_features_enabled:
                self.__manage_uniqueness_for_field__(instance, value)
            instance.__dict__[self._name] = value
            if TypedPyDefaults.uniqueness_features_enabled:
                instance.__manage__uniqueness_of_all_fields__()
        if getattr(instance, "_instantiated", False) and not getattr(
                instance, "_skip_validation", False
        ):
            instance.__validate__()

    def __serialize__(self, value):
        return value

    def __str__(self):
        def as_str(the_val):
            """
            convert to string or a list of strings
            :param the_val: a Field or a list of Fields
            :return: a string representation
            """
            if hasattr(the_val, "__iter__"):
                return f"[{', '.join([str(v) for v in the_val])}]"
            return str(the_val)

        name = self.__class__.__name__
        props = []
        for k, val in sorted(self.__dict__.items()):
            if val is not None and not k.startswith("_"):
                strv = f"'{val}'" if isinstance(val, str) else as_str(val)
                props.append(f"{k} = {strv}")

        propst = f". Properties: {', '.join(props)}" if props else ""
        return f"<{name}{propst}>"

    def _set_immutable(self, immutable: bool):
        self._immutable = immutable

    def serialize(self, value):
        if isinstance(value, (int, float, str, bool)) or value is None:
            return value
        if isinstance(value, list):
            return [self.serialize(v) for v in value]
        return json.dumps(value)

    @property
    def get_type(self):
        return typing.Any

    def to_json_schema(self) -> dict:
        ...

    @classmethod
    def from_json_schema(cls, schema: dict):
        return None


class TypedField(Field):
    """
    A strictly typed base field.
    Should not be used directly. Instead, use :func:`create_typed_field`
    """

    _ty = object

    def _validate(self, value):
        def err_prefix():
            return f"{self._name}: " if self._name else ""

        if not isinstance(value, self._ty):
            raise TypeError(f"{err_prefix()}Expected {self._ty}; Got {wrap_val(value)}")

    def __set__(self, instance, value):
        if not getattr(instance, "_skip_validation", False) and not getattr(
                instance, "_trust_supplied_values", False
        ):
            self._validate(value)
        super().__set__(instance, value)

    @property
    def get_type(self):
        return self.__class__._ty


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
        if isinstance(the_class, StructMeta):
            field_names = getattr(the_class, "_fields", [])
            field_by_name = {k: getattr(the_class, k) for k in field_names}
            all_fields_by_name.update(field_by_name)
    return all_fields_by_name


def _get_all_values_of_attribute(cls, attr_name: str):
    all_classes = reversed([c for c in cls.mro() if isinstance(c, StructMeta)])
    all_values = []
    for the_class in all_classes:
        if isinstance(the_class, StructMeta):
            attr = getattr(the_class, attr_name, None)
            if isinstance(attr, list):
                all_values.extend(attr)
            elif attr is not None:
                all_values.append(attr)
    return all_values


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
            if isinstance(defaults[field_name], (list, dict, set)):
                raise ValueError(
                    f"{field_name}: Got a mutable value as default. This is a bug. "
                    "Instead, use a generating function."
                )
            default_value = (
                defaults[field_name]()
                if callable(defaults[field_name])
                else defaults[field_name]
            )
            cls_dict[field_name]._try_default_value(default_value)
            cls_dict[field_name]._default = defaults[field_name]
        if getattr(cls_dict[field_name], "_default", None) is not None:
            if field_name in required_fields:
                required_fields.remove(field_name)
        elif not required_fields_predefined:
            if field_name not in optional_fields:
                required_fields.add(field_name)
    cls_dict[REQUIRED_FIELDS] = list(required_fields)


def _block_invalid_consts(cls_dict):
    annotations = cls_dict.get("__annotations__", {})
    known_attributes = (
            annotations.keys()
            | SPECIAL_ATTRIBUTES
            | {"_fields", "_fail_fast", "_field_by_name", "_constants"}
    )
    ""
    for k, v in cls_dict.items():
        if (
                k in known_attributes
                or _is_dunder(k)
                or k.startswith(CUSTOM_ATTRIBUTE_MARKER)
        ):
            continue
        if isinstance(v, (bool, list, dict)):
            raise ValueError(f"attribute {k} is not a valid TypedPy attribute.")


class StructMeta(type):
    """
    Metaclass for Structure. Manipulates it to ensure the fields are set up correctly.
    """

    @classmethod
    def __prepare__(cls, name, bases):
        return OrderedDict()

    def __new__(
            cls, name, bases, cls_dict
    ):  # pylint: disable=too-many-locals, too-many-branches
        bases_params, bases_required = get_base_info(bases)
        add_annotations_to_class_dict(cls_dict, previous_frame=currentframe().f_back)
        defaults = cls_dict[DEFAULTS]
        _instantiate_fields_if_needed(cls_dict=cls_dict, defaults=defaults)

        for key, val in cls_dict.items():
            if isinstance(val, StructMeta) and not isinstance(val, Field):
                cls_dict[key] = ClassReference(val)
        fields = [
            key for key, val in cls_dict.items() if isinstance(val, (Field, Constant))
        ]
        for field_name in fields:
            if field_name.startswith("_") or field_name == "kwargs":
                raise ValueError(f"{field_name}: invalid field name")
            if isinstance(cls_dict[field_name], Field):
                setattr(cls_dict[field_name], "_name", field_name)

        for key, val in cls_dict.items():
            if (
                    not any([_is_sunder(key), _is_dunder(key), isinstance(val, Field)])
                    and (isinstance(val, type) or type_is_generic(val))
                    and Structure.is_non_typedpy_field_assignment_blocked()
            ):
                raise TypeError(f"{key}: assigned a non-Typedpy type: {val}")
        _apply_default_and_update_required_not_to_include_fields_with_defaults(
            cls_dict=cls_dict, defaults=defaults, fields=fields
        )

        cls_dict.pop(DEFAULTS, None)
        clsobj = super().__new__(cls, name, bases, dict(cls_dict))
        _check_for_final_violations(clsobj.mro())
        clsobj._fields = fields

        if hasattr(clsobj, "__annotations__"):
            for key, val in _get_all_fields_by_name(clsobj).items():
                if key not in clsobj.__annotations__ and isinstance(val, TypedField):
                    clsobj.__annotations__[key] = getattr(val, "_ty")

        all_fields = set(bases_required + fields) if bases_params else fields
        default_required = list(all_fields)

        clsobj._constants = {}
        for fname in _get_all_fields_by_name(clsobj):
            if isinstance(getattr(clsobj, fname), Constant):
                const_val = getattr(clsobj, fname)._val
                if not isinstance(const_val, (int, str, bool, enum.Enum, float)):
                    raise TypeError(
                        f"Constant {fname} is of an invalid type. Supported "
                        "types are : None, int, str, bool, enum.Enum, float"
                    )
                clsobj._constants[fname] = getattr(clsobj, fname)._val

        required = cls_dict.get(REQUIRED_FIELDS, default_required)
        setattr(clsobj, REQUIRED_FIELDS, list(set(bases_required + required)))
        optional_fields = cls_dict.get(OPTIONAL_FIELDS, [])
        for f in optional_fields:
            if f in required or f in bases_required:
                raise ValueError(
                    "optional cannot override prior required in the class or in a base class"
                )
        if TypedPyDefaults.block_unknown_consts:
            _block_invalid_consts(cls_dict)

        if OLD_ADDITIONAL_PROPERTIES in cls_dict:
            cls_dict[ADDITIONAL_PROPERTIES] = cls_dict[OLD_ADDITIONAL_PROPERTIES]
            setattr(clsobj, ADDITIONAL_PROPERTIES, cls_dict[ADDITIONAL_PROPERTIES])
            delattr(clsobj, OLD_ADDITIONAL_PROPERTIES)
        additional_props = cls_dict.get(
            ADDITIONAL_PROPERTIES, TypedPyDefaults.additional_properties_default
        )

        sig = make_signature(
            clsobj._fields,
            required=required,
            additional_properties=additional_props,
            bases_params_by_name=bases_params,
            bases_required=bases_required,
            constants=clsobj._constants.keys(),
        )
        field_by_name = _get_all_fields_by_name(clsobj)
        setattr(clsobj, "__signature__", sig)
        setattr(clsobj, "_field_by_name", field_by_name)
        return clsobj

    def __str__(cls):
        name = cls.__name__
        props = []
        for k, val in sorted(cls.__dict__.items()):
            if val is not None and not k.startswith("_"):
                strv = f"'{val}'" if isinstance(val, str) else str(val)
                props.append(f"{k} = {strv}")
        props_list = ", ".join(props)
        return f"<Structure: {name}. Properties: {props_list}>"


def _get_mapped_args(v, mapped_type):
    from typedpy.fields import AnyOf

    args_raw = getattr(v, "__args__", None)
    if not args_raw:
        return []
    mapped_args = [
        get_typing_lib_info(a) for a in args_raw if not isinstance(a, typing.TypeVar)
    ]
    if not all(mapped_args):
        if mapped_type is AnyOf:
            for i, arg in enumerate(mapped_args):
                if arg is None:
                    if isinstance(args_raw[i], type):
                        mapped_args[i] = Field[args_raw[i]]
                    else:
                        raise TypeError(f"invalid type {v}")
        else:
            raise TypeError(f"invalid type {v}")
    return mapped_args


def _mapped_type_of_mapped_args(mapped_type, mapped_args):
    from typedpy.fields import AnyOf

    if mapped_args:
        if mapped_type is AnyOf:
            return mapped_type(fields=mapped_args)
        mapped_args = mapped_args if len(mapped_args) > 1 else mapped_args[0]
        return mapped_type(items=mapped_args)
    return mapped_type()


def get_typing_lib_info(v):
    if v is type(None):
        return NoneField()
    if isinstance(v, Field):
        return v
    if inspect.isclass(v) and issubclass(v, Field):
        return v()

    if isinstance(v, StructMeta) and not isinstance(v, Field):
        return ClassReference(v)

    if (
            inspect.isclass(v)
            and issubclass(v, enum.Enum)
            and TypedPyDefaults.automatic_enum_conversion
    ):
        from typedpy.fields import Enum as TypedpyEnum

        return TypedpyEnum(values=v)
    if not type_is_generic(v):
        return convert_basic_types(v)
    origin = getattr(v, "__origin__", None)
    mapped_type = convert_basic_types(origin)
    if mapped_type is None:
        raise TypeError(f"{v} type is not supported")
    mapped_args = _get_mapped_args(v, mapped_type)
    if not mapped_args:
        return mapped_type()
    return _mapped_type_of_mapped_args(mapped_type, mapped_args)


def is_simple_field_annotation(v):
    first_arg = getattr(v, "__args__", [0])[0]
    mros = getattr(first_arg, "__mro__", getattr(v, "__mro__", []))
    return not type_is_generic(v) and (
            isinstance(v, (Field, Structure))
            or Field in mros
            or Structure in mros
            or is_function_returning_field(v)
    )


def add_annotations_to_class_dict(cls_dict, previous_frame):
    annotations = cls_dict.get("__annotations__", {})
    defaults = {}
    optional_fields = set(cls_dict.get(OPTIONAL_FIELDS, []))
    if isinstance(annotations, dict):
        for k, v in annotations.items():
            if k.startswith(CUSTOM_ATTRIBUTE_MARKER):
                continue
            v = _evaluate_if_future_annotations(cls_dict, previous_frame, v)

            if is_simple_field_annotation(v):
                if k in cls_dict:
                    defaults[k] = cls_dict[k]
                cls_dict[k] = v
            else:
                the_type = get_typing_lib_info(v)
                if the_type:
                    _handle_typing_optional(k, optional_fields, the_type)
                    the_type = _type_with_default_value_if_exists(
                        cls_dict, defaults, k, the_type
                    )
                    cls_dict[k] = the_type
    if optional_fields:
        cls_dict[OPTIONAL_FIELDS] = optional_fields
    cls_dict[DEFAULTS] = defaults


def _type_with_default_value_if_exists(cls_dict, defaults, field_name, the_type):
    if field_name in cls_dict:
        default = cls_dict[field_name]
        default_value = default() if callable(default) else default
        try:
            if isinstance(the_type, Field):
                the_type._try_default_value(default_value)
            else:
                the_type = the_type(default=default_value)
        except Exception as e:
            raise e.__class__(f"{field_name}: {str(e)}") from e
        defaults[field_name] = cls_dict[field_name]
    return the_type


def _handle_typing_optional(k, optional_fields, the_type):
    from typedpy.fields import AnyOf

    if isinstance(the_type, AnyOf) and getattr(the_type, "_is_optional", False):
        optional_fields.add(k)


def _evaluate_if_future_annotations(cls_dict, previous_frame, v):
    if isinstance(v, str) and len(v) < 50:
        # The evil eval is to accommodate "from __future__ import annotations".
        module_name = cls_dict["__module__"]
        globals_from_modules = (
            sys.modules[module_name].__dict__ if module_name in sys.modules else None
        )
        v = eval(  # pylint: disable=eval-used
            v,
            globals_from_modules,
            previous_frame.f_locals,
        )
    return v


def convert_field_type_if_possible(the_field):
    first_arg = getattr(the_field, "__args__", [0])[0]
    mros = getattr(first_arg, "__mro__", getattr(the_field, "__mro__", []))
    if not type_is_generic(the_field) and (
            isinstance(the_field, (Field, Structure)) or Field in mros or Structure in mros
    ):
        return the_field
    else:
        return get_typing_lib_info(the_field)


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


        _additiona_properties(bool): optional
            Is it allowed to add additional properties that are not defined in the class definition?
            the default is True. This replaces the old _additionalProperties setting, which is still supported.
            Example:

            .. code-block:: python

                class Foo(Structure):
                    _additional_properties = False

                    id = Integer

                # this is valid:
                Foo(id = 1)

                # this raises an exception:
                Foo(id = 1, a = 2)

        _ignore_none(bool): optional
             Ignore assignment to None for any field value.
             Default is False.
             Required fields never ignore None (since they are required)

        _serialization_mapper(dict or mapper): optional
             mapper for the purpose of serialization/deserialization
             if no _deserialization_mapper is defined, it is also
             used for deserialization.
             Example:

             .. code-block:: python

                class Foo(Structure):
                    i: int
                    _serialization_mapper = {"i": "j"}

                class Bar(Foo):
                    a: Array
                    _serialization_mapper = mappers.TO_LOWERCASE

                assert Deserializer(Bar).deserialize(
                  {"J": 5, "A": [1, 2, 3]}, keep_undefined=False
                ) == Bar(i=5, a=[1, 2, 3])

        _deserializatin_mapper(dict or mapper): optional
            mapper specifically for deserialization, in case you need to differentiate between
            serialization and deserialization mappers.

    Decorating it with @unique ensures that no all instances of this structure will be unique. It
    will raise an exception otherwise (see "Uniqueness" section).
    """

    _fields = []
    _fail_fast = True

    def __init__(self, *args, **kwargs):
        if getattr(self, "_trust_supplied_values", False):
            field_by_name = self.__class__.get_all_fields_by_name()
            for key, value in kwargs.items():
                if (
                        TypedPyDefaults.safe_trusted_instantiation
                        and key in field_by_name
                        and hasattr(field_by_name[key], "_from_trusted_value")
                ):
                    value = field_by_name[key]._from_trusted_value(value, self)
                self.__dict__[key] = value
                self.__dict__["_instantiated"] = True
                self.__dict__["_none_fields"] = set()
                super().__init__()
            return
        try:
            bound = getattr(self, "__signature__").bind(*args, **kwargs)
        except TypeError as ex:
            raise TypeError(f"{self.__class__.__name__}: {ex}")
        if "kwargs" in bound.arguments:
            for name, val in bound.arguments["kwargs"].items():
                setattr(self, name, val)
            del bound.arguments["kwargs"]

        field_by_name = self.get_all_fields_by_name()
        defaults_fields = [
            key
            for key, value in field_by_name.items()
            if getattr(value, "_default", None) is not None
               and key not in bound.arguments
        ]

        setattr(self, "_none_fields", set())
        for field_name, const_val in getattr(self, "_constants", {}).items():
            if field_name in kwargs:
                raise ValueError(
                    f"{self.__class__.__name__}:  {field_name} is defined as a constant. It cannot be set."
                )
            setattr(self, field_name, const_val)

        self._set_defaults(defaults_fields, field_by_name)

        if Structure.failing_fast():
            for name, val in bound.arguments.items():
                try:
                    if val is not Undefined:
                        setattr(self, name, val)
                except Exception as e:
                    if isinstance(e, JSONDecodeError):
                        raise e
                    cls_name = self.__class__.__name__
                    raise e.__class__(f"{cls_name}.{e}") from e
        else:
            errors = []
            for name, val in bound.arguments.items():
                try:
                    setattr(self, name, val)
                except (TypeError, ValueError) as ex:
                    errors.append(ex)
            raise_errs_if_needed(self.__class__, errors)

        self.__validate__()
        self._instantiated = True
        if TypedPyDefaults.uniqueness_features_enabled:
            self.__manage_uniqueness__()
            self.__manage__uniqueness_of_all_fields__()
        super().__init__()

    def _set_defaults(self, defaults_fields, field_by_name):
        for field_name in defaults_fields:
            default = getattr(field_by_name[field_name], "_default")
            default_value = default() if callable(default) else default
            setattr(self, field_name, default_value)

    def __manage__uniqueness_of_all_fields__(self):
        fields_by_name = self.__class__.get_all_fields_by_name()
        for name, field in fields_by_name.items():
            if not isinstance(field, Constant) and field.defined_as_unique():
                field.__manage_uniqueness_for_field__(self, getattr(self, name, None))

    def __setattr__(self, key, value):
        if getattr(self, "_trust_supplied_values", False):
            super().__setattr__(key, value)
            return

        if getattr(self, IS_IMMUTABLE, False):
            if getattr(self, "_instantiated", False):
                raise ValueError(f"{self.__class__.__name__}: Structure is immutable")
            if not getattr(value, IS_IMMUTABLE, False):
                needs_defensive_copy = not isinstance(
                    value,
                    (
                        ImmutableMixin,
                        int,
                        float,
                        str,
                        bool,
                        enum.Enum,
                        ImmutableStructure,
                    ),
                )
                value = deepcopy(value) if needs_defensive_copy else value

        if key in getattr(self, "_constants", {}) and getattr(
                self, "_instantiated", False
        ):
            raise ValueError(
                f"{self.__class__.__name__}:  {key} is defined as a constant. It cannot be set."
            )
        if not any(
                [
                    getattr(
                        self,
                        ADDITIONAL_PROPERTIES,
                        TypedPyDefaults.additional_properties_default,
                    ),
                    key in self.get_all_fields_by_name(),
                    _is_sunder(key),
                    _is_dunder(key),
                ]
        ):
            raise ValueError(
                f"{self.__class__.__name__}: trying to set a non-field '{key}' is not allowed"
            )
        if all(
                [
                    getattr(
                        self, IGNORE_NONE_VALUES, TypedPyDefaults.allow_none_for_optionals
                    )
                    or getattr(self, ENABLE_UNDEFINED, False),
                    value is None,
                    key not in getattr(self.__class__, REQUIRED_FIELDS, []),
                ]
        ):
            if key in self.get_all_fields_by_name() and getattr(
                    self, ENABLE_UNDEFINED, False
            ):
                getattr(self, "_none_fields").add(key)
            return

        if (
                key in self.get_all_fields_by_name()
                and getattr(self, ENABLE_UNDEFINED, False)
                and value is not None
        ):
            getattr(self, "_none_fields").discard(key)
        super().__setattr__(key, value)

        if (
                TypedPyDefaults.uniqueness_features_enabled
                and getattr(self, "_instantiated", False)
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
            as_strings = [f"{to_str(k)} = {to_str(v)}" for (k, v) in values.items()]
            return ",".join(as_strings)

        def to_str(the_val):
            if isinstance(the_val, list):
                return f"[{list_to_str(the_val)}]"
            if isinstance(the_val, tuple):
                return f"({list_to_str(the_val)})"
            if isinstance(the_val, set):
                return f"{{{list_to_str(the_val)}}}"
            if isinstance(the_val, dict):
                return f"{{{dict_to_str(the_val)}}}"
            return str(the_val)

        name = self.__class__.__name__
        if name.startswith("StructureReference_") and self.__class__.__bases__ == (
                Structure,
        ):
            name = "Structure"
        props = []
        for k, val in sorted(self.__dict__.items()):
            if k not in _internal_props:
                strv = f"'{val}'" if isinstance(val, str) else to_str(val)
                props.append(f"{k} = {strv}")
        for k in sorted((getattr(self, "_none_fields", []))):
            props.append(f"{k} = None")
        props_list = ", ".join(props)
        return f"<Instance of {name}. Properties: {props_list}>"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        merged = {**self.__dict__, **other.__dict__}
        for k in sorted(merged):
            if k in _internal_props:
                continue
            if k in self.__class__.get_all_fields_by_name():
                if getattr(self, k) != getattr(other, k):
                    return False
            else:
                if self.__dict__.get(k) != other.__dict__.get(k):
                    return False

        self_nones = self.__dict__.get("_none_fields")
        other_nones = other.__dict__.get("_none_fields")
        if (self_nones or other_nones) and self_nones != other_nones:
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
            raise ValueError(f"{key} is mandatory")
        del self.__dict__[key]

    def __validate__(self):
        pass

    def __deepcopy__(self, memo):
        if isinstance(
                self,
                (
                        int,
                        float,
                        str,
                        tuple,
                        bool,
                        enum.Enum,
                        ImmutableMixin,
                        ImmutableStructure,
                ),
        ) and getattr(self, IS_IMMUTABLE, False):
            return self
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        result._skip_validation = True  # pylint: disable=attribute-defined-outside-init
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
        return [k for k in sorted(self.__dict__) if k not in _internal_props]

    def __bool__(self):
        return any(
            v is not None for k, v in self.__dict__.items() if k not in _internal_props
        )

    def _additional_serialization(self) -> dict:
        """
        :return: additional fields when serializing a structure,
            Each key is a key in the output json, and each value
            can either be a function with no parameters, a method, or a
            simple value
        """
        if callable(getattr(super(), "_additional_serialization", None)):
            return super()._additional_serialization()
        return {}

    @classmethod
    def get_all_fields_by_name(cls) -> dict:
        return getattr(cls, "_field_by_name")

    @classmethod
    def get_aggregated_serialization_mapper(cls) -> list:
        return _get_all_values_of_attribute(cls, SERIALIZATION_MAPPER)

    @classmethod
    def get_aggregated_deserialization_mapper(cls) -> list:
        all_classes = reversed([c for c in cls.mro() if isinstance(c, StructMeta)])
        all_values = []
        for the_class in all_classes:
            if issubclass(the_class, Structure):
                deserialization_mapper = getattr(
                    the_class, DESERIALIZATION_MAPPER, None
                )
                attr = (
                    deserialization_mapper
                    if deserialization_mapper is not None
                    else getattr(the_class, SERIALIZATION_MAPPER, None)
                )
                if isinstance(attr, list):
                    all_values.extend(attr)
                elif attr is not None:
                    all_values.append(attr)
        return all_values

    def _is_wrapper(self):
        field_by_name = _get_all_fields_by_name(self.__class__)
        field_names = list(field_by_name.keys())
        props = self.__class__.__dict__
        required = props.get(REQUIRED_FIELDS, field_names)
        additional_props = props.get(
            ADDITIONAL_PROPERTIES, TypedPyDefaults.additional_properties_default
        )
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

        raise TypeError(f"{self.__class__.__name__} does not support this operator")

    def __iter__(self):
        field_by_name = _get_all_fields_by_name(self.__class__)
        field_names = list(field_by_name.keys())
        val = getattr(self, field_names[0], {})

        if self._is_wrapper() and hasattr(val, "__iter__"):
            return iter(val)
        raise TypeError(f"{self.__class__.__name__} is not a wrapper of an iterable")

    def shallow_clone_with_overrides(self, **kw):
        fields_names = self.get_all_fields_by_name().keys()
        field_value_by_name = {
            f: getattr(self, f)
            for f in fields_names
            if (getattr(self, f) is not None or f in getattr(self, "_none_fields"))
               and f not in getattr(self.__class__, "_constants", {})
        }
        kw_args = {
            **{k: v for k, v in field_value_by_name.items() if v is not Undefined},
            **kw,
        }
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
                        and not issubclass(self.__class__, ImmutableStructure)
                        or issubclass(self.__class__, ImmutableStructure)
                        and not issubclass(cls, ImmutableStructure)
                )
                else self
            )

            fields_names = cls.get_all_fields_by_name().keys()
            field_value_by_name = {
                f: getattr(that, f)
                for f in fields_names
                if getattr(that, f, None) is not None
            }
            return cls(
                **{k: v for k, v in field_value_by_name.items() if v is not Undefined}
            )

        raise TypeError(f"cls must be subclass of {self.__class__.__name__}")

    def to_other_class(self, target_class: type(T), *, ignore_props=None, **kw) -> T:
        """
        Shallow copy of the fields in the structure and instantiate an instance of the given target_class
        Arguments:
            target_class:
                The target class of the new object to be instantiated from this structure.
                This does not need to be a class:`Structure`.

                Example:

                .. code-block:: python
                    class Person:
                        def __init__(self ,* ,name, age):
                            ...

                    class Foo(Structure):
                        id = Integer
                        name = String

                    person = Foo(id=1, name="john").to_other_class(Person, ignore_props=["id"], age=40)
                    assert person.age == 40
                    assert.person.name == "john"

            ignore_props(list[str]): optional
                a list of field names to be ignored (not copied).

            kw: optional
                any overrides of attributes. For example: "age="40" in the code snippet above

        Returns:
            A new instance of the provided target_class with all the attributes of the current structure,
            except the ones state in the ignore_props parameters, and also the attributes overrides given in
            the keyword arguments.
            :param ignore_props:
        """

        ignore_props = ignore_props if ignore_props else []
        args_from_structure = {
            k: getattr(self, k, None)
            for k in self.get_all_fields_by_name()
            if k not in ignore_props
               and k not in getattr(self.__class__, "_constants", {})
        }

        kwargs = {
            **{k: v for k, v in args_from_structure.items() if v is not Undefined},
            **{k: v for k, v in kw.items() if v is not Undefined},
        }
        return target_class(**kwargs)

    @classmethod
    def from_other_class(cls, source_object, *, ignore_props=None, **kw):
        """
        Return a new instance of the current :class:`Structure`, with the attributes of the source_object.
        The optional parameters allow to ignore/override attributes.
        For example:

        .. code-block:: python
                    class PersonModel:
                        def __init__(self ,* ,first_name, age):
                            ...

                    class Person(Structure):
                        id = Integer
                        name = String
                        age = Integer

                    person_model = PersonModel(first_name="john", age=40)
                    person = Person.from_other_class(
                        person_model,
                        id=123,
                        name=person_model.first_name
                    )
                    assert person == Person(name="john", id=123, age=40)

        Arguments:
            source_object:
                The source object to be copied from. Can be of any type that has
                attributes with the names of the expected fields

            ignore_props(list[str]): optional
                The field names to ignore (not copy)

            kw: optional
                explicit overrides/additional field mapping. In the snippet above we
                set the "id" and "name" fields directly.

        Returns:
            The new instance of the current structure type, with the fields set.
        """

        is_mapping = isinstance(source_object, Mapping)

        def extract_attr(k):
            return source_object.get(k) if is_mapping else getattr(source_object, k, None)

        ignore_props = ignore_props if ignore_props else []
        args_from_model = {
            k: extract_attr(k)
            for k in cls.get_all_fields_by_name()
            if k not in ignore_props
               and k not in getattr(cls, "_constants", {})
               and (hasattr(source_object, k) or is_mapping)
        }
        kwargs = {
            **{k: v for k, v in args_from_model.items() if v is not Undefined},
            **{k: v for k, v in kw.items() if v is not Undefined},
        }
        try:
            return cls(**kwargs)
        except TypeError as e:
            if f"{cls.__name__}: missing a required argument" in str(e):
                raise TypeError(f"You provided an instance of {source_object.__class__}, "
                                f"that does not have all the required fields of {cls.__name__}") from e
            else:
                raise e

    @classmethod
    def from_trusted_data(cls, source_object=None, *, ignore_props=None, **kw):
        """
        Like from_other_class, but "trusts" the input and skips any validation.
        This should be used when you trust the input, and performance is more
        important.

         Arguments:
            source_object:
                The source object to be copied from. Can be of any type, including
                Mapping.

            ignore_props(list[str]): optional
                The field names to ignore (not copy)

            kw: optional
                explicit overrides/additional field mapping. In the snippet above we
                set the "id" and "name" fields directly.
        Returns:
            The new instance of the current structure type, with the fields set.
            However, there is no validation: garbage-in => garbage-out
        """
        if source_object:
            ignore_props = ignore_props if ignore_props else []
            is_mapping = isinstance(source_object, Mapping)
            args_from_model = {
                k: source_object.get(k, None)
                if is_mapping
                else getattr(source_object, k, None)
                for k in cls.get_all_fields_by_name()
                if k not in ignore_props
                   and k not in getattr(cls, "_constants", {})
                   and (not is_mapping or k in source_object)
            }
            kwargs = {
                **{k: v for k, v in args_from_model.items() if v is not Undefined},
                **kw,
            }
        else:
            kwargs = kw
        obj = cls.__new__(cls)
        setattr(obj, "_trust_supplied_values", True)
        obj.__init__(**kwargs)
        return obj

    def used_trusted_instantiation(self) -> bool:
        """
        Was this instance created with trusted instantiation?
        This is useful when you want to check if your Structure is compatible
        with trusted deserialization.
        """
        return getattr(self, "_trust_supplied_values", False)

    @classmethod
    def trust_supplied_values(cls, trust=True):
        """
        Mark the class as trusting supplied
        """
        cls._trust_supplied_values = trust

    @staticmethod
    def set_fail_fast(fast_fail: bool):
        Structure._fail_fast = fast_fail

    @staticmethod
    def failing_fast():
        return Structure._fail_fast

    @staticmethod
    def set_additional_properties_default(additional_props: bool = True):
        TypedPyDefaults.additional_properties_default = additional_props

    @staticmethod
    def set_compact_serialization_default(compact_serialization_default: bool = False):
        TypedPyDefaults.compact_serialization_default = compact_serialization_default

    @staticmethod
    def set_compact_deserialization_default(compact_deserialization_default: bool = False):
        TypedPyDefaults.compact_deserialization_default = compact_deserialization_default

    @staticmethod
    def set_auto_enum_conversion(flag: bool = True):
        TypedPyDefaults.automatic_enum_conversion = flag

    @staticmethod
    def set_block_non_typedpy_field_assignment(flag=True):
        Structure._block_non_typedpy_field_assignment = flag

    @staticmethod
    def is_non_typedpy_field_assignment_blocked():
        return getattr(Structure, "_block_non_typedpy_field_assignment", True)

    @classmethod
    def omit(cls, *fields_to_omit, class_name: str = ""):
        """
        Define a new Structure class with all the fields of the given class, except for the omitted ones.
         For Example:

         .. code-block:: python

             class Foo(ImmutableStructure):
                i: int
                d: dict[str, int] = dict
                s: set
                a: str
                b: Integer

             class Bar(Foo.omit("a", "b")):
                x: int

        "Bar" has the fields: i, d, s, x. Note that Bar does not extend Foo, but it is a Structure class.
         It does copy attributes like serialization mappers, _ignore_none,
        but Bar can override any of them.

        Another valid usage:

        .. code-block:: python

            Bar = Foo.omit("a", "b", "i", "s")
            bar = Bar(d={"a": 5})

        """

        cls_dict = _init_class_dict(cls)
        cls_dict[REQUIRED_FIELDS] = [
            x for x in getattr(cls, REQUIRED_FIELDS) if x not in fields_to_omit
        ]
        for k in fields_to_omit:
            if k not in cls.get_all_fields_by_name():
                raise TypeError(f"Omit: {wrap_val(k)} is not a field of {cls.__name__}")

        for k, v in cls.get_all_fields_by_name().items():
            if k not in fields_to_omit:
                cls_dict[k] = v

        classname = class_name if class_name else f"Omit{cls.__name__}"
        newclass = type(classname, (Structure,), cls_dict)

        return newclass

    @classmethod
    def pick(cls, *fields_to_pick, class_name: str = ""):
        """
        Define a new Structure class with that picks specific fields from a predefined class.
         For Example:

         .. code-block:: python

             class Foo(ImmutableStructure):
                i: int
                d: dict[str, int] = dict
                s: set
                a: str
                b: Integer

             class Bar(Foo.pick("a", "b")):
                x: int

        "Bar" has the fields: a, b, x. Note that Bar does not extend Foo, but it is a Structure class.
         It does copy attributes like serialization mappers, _ignore_none,
        but Bar can override any of them.

        Another valid usage:

        .. code-block:: python

            Bar = Foo.pick("d")
            bar = Bar(d={"a": 5})

        """
        cls_dict = _init_class_dict(cls)
        reference_class_fields = cls.get_all_fields_by_name()
        for k in fields_to_pick:
            if k not in reference_class_fields:
                raise TypeError(f"Pick: {wrap_val(k)} is not a field of {cls.__name__}")
            cls_dict[k] = reference_class_fields[k]
        cls_dict[REQUIRED_FIELDS] = [
            x for x in getattr(cls, REQUIRED_FIELDS) if x in fields_to_pick
        ]

        classname = class_name if class_name else f"Pick{cls.__name__}"
        newclass = type(classname, (Structure,), cls_dict)

        return newclass


def _init_class_dict(cls):
    attributes_to_include = {
        "_fields",
        IGNORE_NONE_VALUES,
        DEFAULTS,
    }
    cls_dict = {}
    for k, v in cls.__dict__.items():
        if k in attributes_to_include:
            cls_dict[k] = v

    return cls_dict


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

    def serialize(self, value):
        return None


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
        return f"<ClassReference: {self._ty.__name__}>"

    @property
    def get_type(self):
        return self._ty

    def serialize(self, value):
        serializer = getattr(self._ty, "serialize", None)
        return serializer(value)


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
