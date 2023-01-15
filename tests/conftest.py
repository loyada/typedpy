# from typedpy.testing import  pytest_assertrepr_compare
import pytest

from typedpy import Structure
from typedpy.structures import TypedPyDefaults

@pytest.fixture(name="additional_props_default_is_false")
def fixture_additional_props_default_is_false():
    Structure.set_additional_properties_default(False)
    yield
    Structure.set_additional_properties_default(True)


@pytest.fixture(name="compact_serialization")
def fixture_compact_serialization():
    Structure.set_compact_serialization_default(True)
    yield
    Structure.set_compact_serialization_default(False)


@pytest.fixture(name="auto_conversion_of_enums")
def fixture_auto_conversion_of_enums():
    Structure.set_auto_enum_conversion(True)
    yield
    Structure.set_auto_enum_conversion(False)


@pytest.fixture(name="uniqueness_enabled")
def fixture_uniqueness_enabled():
    TypedPyDefaults.uniqueness_features_enabled = True
    yield
    TypedPyDefaults.uniqueness_features_enabled = False


@pytest.fixture(name="allow_none_for_optional")
def fixture_allow_none_for_optional():
    TypedPyDefaults.allow_none_for_optionals = True
    yield
    TypedPyDefaults.allow_none_for_optionals = False


@pytest.fixture(name="no_defensive_copy_on_get")
def fixture_no_defensive_copy_on_get():
    TypedPyDefaults.defensive_copy_on_get = False
    yield
    TypedPyDefaults.defensive_copy_on_get = True


