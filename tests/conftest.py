# from typedpy.testing import  pytest_assertrepr_compare
import pytest

from typedpy import Structure


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
