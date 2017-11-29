from pytest import raises

from typedpy import StructureReference, Structure, String, Integer, Number, PositiveInt


class Person(Structure):
    _required = ['ssid']
    name = String(pattern='[A-Za-z]+$', maxLength=8)
    ssid = String(minLength=3, pattern='[A-Za-z]+$')
    num = Integer(maximum=30, minimum=10, multiplesOf="dd", exclusiveMaximum=False)
    foo = StructureReference(a=String(), b = StructureReference(c = Number(minimum=10), d = Number(maximum=10)))

# Inherited Structure. Note:
# - adding a new attribute "children"
# - overriding attribute "num" from Person to a new type
# - expecting the required fields to be: ssid (from Person), children, num
# - attributes ssid, foo, name are inherited from num
class OldPerson(Person):
    _additionalProperties = False
    children = PositiveInt()
    num = PositiveInt()


def test_str_OldPerson():
    assert str(OldPerson)=="<Structure: OldPerson. Properties: children = <PositiveInt>, num = <PositiveInt>>"

def test_str_OldPerson_instance():
    op = OldPerson(children=1, num=1, ssid="aaa", name = "abc")
    assert str(op)=="<Instance of OldPerson. Properties: children = 1, name = 'abc', num = 1, ssid = 'aaa'>"

def test_missing_inherited_required_property_err():
    with raises(TypeError) as excinfo:
        OldPerson(children=1, num=1, name="abc")
    assert "missing a required argument: 'ssid'" in str(excinfo.value) or \
           "'ssid' parameter lacking default value" in str(excinfo.value)

def test_missing_required_property_err():
    with raises(TypeError) as excinfo:
        OldPerson(num=1, name="abc", ssid="aaa")
    assert "missing a required argument: 'children'" in str(excinfo.value) or \
           "'children' parameter lacking default value" in str(excinfo.value)

def test_num_overrides_inherited_num():
    assert OldPerson(num=1, name="abc", ssid="aaa", children=1).num == 1

def test_verifying_inherited_property1():
    with raises(TypeError) as excinfo:
        OldPerson(num=1, name="abc", ssid="aaa", foo="", children=1)
    assert 'foo: Expected a dictionary' in str(excinfo.value)


def test_verifying_inherited_embedded_property1_err():
    with raises(ValueError) as excinfo:
        OldPerson(num=1, name="abc", ssid="aaa", foo={'a': "xyz", 'b': {'c': 5, 'd': 5}}, children=1)
    assert 'c: Expected a minimum of 10' in str(excinfo.value)

def test_verifying_inherited_embedded_property2_err():
    with raises(TypeError) as excinfo:
        OldPerson(num=1, name="abc", ssid="aaa", foo={'b': {'c': 5, 'd': 5}}, children=1)
    assert "missing a required argument: 'a'" in str(excinfo.value) or \
           "'a' parameter lacking default value" in str(excinfo.value)

def test_verifying_inherited_embedded_property_success():
        assert OldPerson(num=1, name="abc", ssid="aaa", foo={'a': 'x', 'b': {'c': 15, 'd': 5}}, children=1).foo.a=='x'

def test_additional_properties_err():
    with raises(TypeError) as excinfo:
        OldPerson(num=1, name="abc", ssid="aaa", children=1, xyz =1)
    assert "got an unexpected keyword argument 'xyz'" in str(excinfo.value) or \
           "too many keyword arguments" in str(excinfo.value)
