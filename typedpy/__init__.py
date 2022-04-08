"""
A type-safe strictly defined structures, compatible with JSON draft 4
but offers significantly more functionality.
"""
from typedpy.structures import (
    Structure,
    Field,
    TypedField,
    ClassReference,
    ImmutableStructure,
    create_typed_field,
    NoneField,
    FinalStructure,
    ImmutableField,
    unique,
    AbstractStructure,
)

from typedpy.structures_reuse import (
    Partial,
    AllFieldsRequired,
    Omit,
    Pick,
    Extend,
)

from typedpy.fields import (
    Number,
    Integer,
    PositiveInt,
    PositiveFloat,
    NonPositiveInt,
    NonPositiveFloat,
    NegativeInt,
    NegativeFloat,
    NonNegativeInt,
    NonNegativeFloat,
    Float,
    Positive,
    Negative,
    NonPositive,
    NonNegative,
    DecimalNumber,
    String,
    SizedString,
    Sized,
    AllOf,
    AnyOf,
    OneOf,
    NotField,
    Boolean,
    Array,
    Set,
    Map,
    Tuple,
    StructureReference,
    Anything,
    SerializableField,
    Function,
    ImmutableMap,
    ImmutableArray,
    ImmutableSet,
    ImmutableFloat,
    ImmutableString,
    ImmutableInteger,
    ImmutableNumber,
    ImmutableDeque,
    Deque,
    ExceptionField,
    Generator,
)

from typedpy.json_schema_mapping import (
    structure_to_schema,
    schema_to_struct_code,
    schema_definitions_to_code,
    write_code_from_schema,
)

from .enum import Enum, EnumString

from .serialization import (
    deserialize_structure,
    serialize,
    serialize_field,
    FunctionCall,
    deserialize_single_field,
    HasTypes,
)

from .serialization_wrappers import (
    Serializer,
    Deserializer,
    deserializer_by_discriminator,
)

from .extfields import (
    DateString,
    DateField,
    DateTime,
    TimeString,
    HostName,
    IPV4,
    JSONString,
    EmailAddress,
)

from .subclass import SubClass

from .errors import (
    standard_readable_error_for_typedpy_exception,
    ErrorInfo,
    get_simplified_error,
)

from .utility import get_list_type, type_is_generic

from .mappers import mappers, Deleted, Constant, DoNotSerialize

from .versioned_mapping import convert_dict, Versioned

from .commons import (
    nested,
    deep_get,
    first_in,
    flatten,
    default_factories,
    InvalidStructureErr,
)

from .keysof import keys_of
from .type_helpers import create_pyi
