from pytest import raises

from typedpy import Structure, AllOf, AnyOf, OneOf, Integer, String, Positive, Number, NotField


class Trade(Structure):
    _additionalProperties = True
    _required = []
    a = AllOf([Number(multiplesOf=5, maximum=20, minimum=-10), Integer, Positive])
    # Can also omit the parens
    b = AnyOf[Number(maximum=20, minimum=-10), Integer(), Positive, String]
    c = OneOf([Number(multiplesOf=5, maximum=20, minimum=-10), Integer, Positive, String])
    d = NotField([Number(multiplesOf=5, maximum=20, minimum=-10), String])
    e = AllOf([])
    broken = AllOf[String, Integer]
    f = NotField[Number]





def test_allof_str():
    assert str(Trade.a)=="<AllOf [<Number. Properties: maximum = 20, minimum = -10, multiplesOf = 5>, <Integer>, <Positive>]>"

def test_allof_empty_str():
        assert str(
            Trade.e) == "<AllOf>"


def test_anyoff_str():
    assert str(Trade.b)=="<AnyOf [<Number. Properties: maximum = 20, minimum = -10>, <Integer>, <Positive>, <String>]>"

def test_oneof_str():
    assert str(Trade.c)=="<OneOf [<Number. Properties: maximum = 20, minimum = -10, multiplesOf = 5>, <Integer>, <Positive>, <String>]>"

def test_notfield_str():
    assert str(Trade.d)=="<NotField [<Number. Properties: maximum = 20, minimum = -10, multiplesOf = 5>, <String>]>"

def test_allof_misses_one_err1():
    with raises(ValueError) as excinfo:
        Trade(a=-5)
    assert "a: Must be positive" in str(excinfo.value)

def test_allof_misses_one_err2():
    with raises(ValueError) as excinfo:
        Trade(a=3)
    assert "a: Expected a a multiple of 5" in str(excinfo.value)

def test_allof_valid():
    assert Trade(a=10).a==10

def test_allof_broken_err1():
    with raises(TypeError):
        Trade(broken=3)

def test_allof_broken_err2():
    with raises(TypeError):
        Trade(broken='a')

def test_anyof_misses_all_err():
    with raises(ValueError) as excinfo:
        Trade(b=-99.1)
    assert "b: Did not match any field option" in str(excinfo.value)

def test_anyof_valid1():
    assert Trade(b=-99).b==-99

def test_anyof_valid2():
    assert Trade(b='xyz').b=='xyz'

def test_anyof_valid3():
    assert Trade(b=-0.111).b==-0.111

def test_anyof_valid4():
    assert Trade(b=999.5).b==999.5

def test_oneof_misses_all_err():
    with raises(ValueError) as excinfo:
        Trade(c=-99.1)
    assert "c: Did not match any field option" in str(excinfo.value)

def test_oneof_matches_few_err():
    with raises(ValueError) as excinfo:
        Trade(c=5)
    assert "c: Matched more than one field option" in str(excinfo.value)

def test_oneof_valid1():
    assert Trade(c=-99).c==-99

def test_oneof_valid2():
    assert Trade(c=99.5).c==99.5

def test_not_matches_err():
    with raises(ValueError) as excinfo:
        Trade(d=5)
    assert "d: Expected not to match any field definition" in str(excinfo.value)

def test_not_valid():
    assert Trade(d=-99.6).d == -99.6

def test_not_single_matches_err():
    with raises(ValueError) as excinfo:
        Trade(f=-5.234)
    assert "f: Expected not to match any field definition" in str(excinfo.value)


def test_not_single_valid():
    assert Trade(f=Integer).f == Integer


def test_simplified_definition_wrong_type_err():
    with raises(TypeError) as excinfo:
        class Example(Structure):
            a = AllOf[Integer, float]
    assert "Expected a Field class or instance" in str(excinfo.value)



def test_standard_definition_wrong_field_type_err():
    with raises(TypeError) as excinfo:
        class Example(Structure):
            a = AllOf([Integer, float])
    assert "Expected a Field class or instance" in str(excinfo.value)


def test_standard_definition_wrong_fields_arg_err():
    with raises(TypeError) as excinfo:
        class Example(Structure):
            a = AllOf(1)
    assert "Expected a Field class or instance" in str(excinfo.value)


