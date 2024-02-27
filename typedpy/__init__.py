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
    keys_of,
)
from typedpy.structures.defaults import TypedPyDefaults

from .json_schema import (
    structure_to_schema,
    schema_to_struct_code,
    schema_definitions_to_code,
    write_code_from_schema,
)


from .serialization import (
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
    create_serializer,
    FastSerializable,
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

from .stubs import (
    create_pyi,
    create_stub_for_file,
    create_stub_for_file_using_ast,
)


from .errors import (
    standard_readable_error_for_typedpy_exception,
    ErrorInfo,
    get_simplified_error,
)

from .utility import get_list_type, type_is_generic

from .fields import *

from .commons import (
    nested,
    deep_get,
    first_in,
    flatten,
    default_factories,
    InvalidStructureErr,
    Constant,
    Undefined,
    INDENT,
)
