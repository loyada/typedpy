import pytest

from typedpy import StructureReference, Structure, String, Number, PositiveInt, Integer


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
    children = PositiveInt()
    num = PositiveInt()

def test_string_with_regex_err():
    with pytest.raises(ValueError) as excinfo:
        Person(name="fo d", ssid="fff", num=25, foo={'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    assert 'name: Does not match regular expression: [A-Za-z]+$' in str(excinfo.value)

def test_string_type_err():
    with pytest.raises(TypeError) as excinfo:
        Person(name="fo", ssid=10, num=30, foo={'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    assert 'ssid: Expected a string' in str(excinfo.value)

def test_number_max_err():
    with pytest.raises(ValueError) as excinfo:
        Person(name="fo", ssid="aaa", num=33, foo={'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    assert 'num: Expected a maxmimum of 30' in str(excinfo.value)

def test_embedded_field_number_min_err():
     with pytest.raises(ValueError) as excinfo:
         Person(name="fo", ssid="aaa", num=10, foo={'a': 'aaa', 'b': {'c': 0, 'd': 1}})
     assert 'c: Expected a minimum of 10' in str(excinfo.value)

def test_embedded_field_number_type_err():
    with pytest.raises(TypeError) as excinfo:
        Person(name="fo", ssid="aaa", num=10, foo={'a': 'aaa', 'b': {'c': "", 'd': 1}})
    assert 'c: Expected a number' in str(excinfo.value)

def test_miss_required_field():
    with pytest.raises(TypeError) as excinfo:
        Person(name="fo", num=10, foo={'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    assert "missing a required argument: 'ssid'" in str(excinfo.value) or \
           "'ssid' parameter lacking default value" in str(excinfo.value)

def test_valid_instance_and_accessor():
    p = Person(name="aaa", ssid="aaa", num=10, foo={'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    assert p.num==10

def test_change_number_to_illegal_val():
    p = Person(name="aaa", ssid="aaa", num=10, foo={'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    with pytest.raises(ValueError) as excinfo:
        p.num -= 1
    assert "num: Expected a minimum of 10" in str(excinfo.value)

def test_valid_instance_and_accessor_of_embedded_val():
    p = Person(name="aaa", ssid="aaa", num=10, foo={'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    assert p.foo.b.d==1

def test_updating_embedded_struct_to_an_invalid_val():
    p = Person(name="aaa", ssid="aaa", num=10, foo={'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    with pytest.raises(TypeError) as excinfo:
        p.foo.b = {'d': 1}
    assert "missing a required argument: 'c'" in str(excinfo.value) or \
           "'c' parameter lacking default value" in str(excinfo.value)

def test_updating_embedded_field_to_an_invalid_val():
    p = Person(name="aaa", ssid="aaa", num=10, foo={'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    with pytest.raises(ValueError) as excinfo:
        p.foo.b.d = 99
    assert 'd: Expected a maxmimum of 10' in str(excinfo.value)

def test_str_Structure():
    assert str(Person)=="<Structure: Person. Properties: foo = <Structure. Properties: a = <String>, b = <Structure. Properties: c = <Number. Properties: " \
                        "minimum = 10>, d = <Number. Properties: maximum = 10>>>, name = <String. Properties: maxLength = 8, pattern = '[A-Za-z]+$'>, num =" \
                        " <Integer. Properties: exclusiveMaximum = False, maximum = 30, minimum = 10, multiplesOf = 'dd'>, ssid = <String. Properties: minLength = 3, pattern = '[A-Za-z]+$'>>"


def test_str_Structure_instance():
    p = Person(name="aaa", ssid="abc", num=10, foo={'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    assert str(p)=="<Instance of Person. Properties: foo = <Instance of Structure. Properties: a = 'aaa', b = <Instance of Structure. Properties: c = 10, d " \
                   "= 1>>, name = 'aaa', num = 10, ssid = 'abc'>"

def test_del_mandatory_err():
    p = Person(name="aaa", ssid="abc", num=10, foo={'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    with pytest.raises(ValueError) as excinfo:
        del p['ssid']
    assert 'ssid is manadoty' in str(excinfo.value)

def test_del_non_mandatory():
    p = Person(name="aaa", ssid="abc", num=10, foo={'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    del p['name']
    assert 'name' not in p.__dict__

