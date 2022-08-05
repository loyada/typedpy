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
    Partial,
    AllFieldsRequired,
    Omit,
    Pick,
    Extend,
    keys_of
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
    Enum,
    EnumString,
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
    SubClass,
    ExceptionField,
    Generator,
    FunctionCall
)

from typedpy.json_schema.json_schema_mapping import (
    structure_to_schema,
    schema_to_struct_code,
    schema_definitions_to_code,
    write_code_from_schema,
)


from typedpy.serialization import (
    Serializer,
    Deserializer,
    deserializer_by_discriminator,
    convert_dict,
    Versioned,
    mappers,
    Deleted,
    DoNotSerialize,
    serialize_field,
    serialize,
    deserialize_structure,
    deserialize_single_field,
    HasTypes,
)

from typedpy.extfields import (
    DateString,
    DateField,
    DateTime,
    TimeString,
    HostName,
    IPV4,
    JSONString,
    EmailAddress,
)


from .errors import (
    standard_readable_error_for_typedpy_exception,
    ErrorInfo,
    get_simplified_error,
)

from .utility import get_list_type, type_is_generic


from .commons import (
    nested,
    deep_get,
    first_in,
    flatten,
    default_factories,
    InvalidStructureErr,
    Constant,
)

from typedpy.stubs import create_pyi, create_stub_for_file, create_stub_for_file_using_ast
