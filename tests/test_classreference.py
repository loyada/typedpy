from pytest import raises

from typedpy import (
    StructureReference,
    Structure,
    ClassReference,
    Number,
    String,
    Integer,
    PositiveInt,
    SizedString,
    Enum,
)


class Person(Structure):
    _required = ["ssid"]
    name = String(pattern="[A-Za-z]+$", maxLength=8)
    ssid = String(minLength=3, pattern="[A-Za-z]+$")
    num = Integer(maximum=30, minimum=10, multiplesOf="dd", exclusiveMaximum=False)
    foo = StructureReference(
        a=String(), b=StructureReference(c=Number(minimum=10), d=Number(maximum=10))
    )


class OldPerson(Person):
    _additionalProperties = False
    children = PositiveInt
    num = PositiveInt


class ExampleBase(Structure):
    a = PositiveInt


class Example(ExampleBase, OldPerson):
    b = String


class Trade(Structure):
    _additionalProperties = True
    _required = ["tradable"]
    tradable = String()
    # class referece: to another Structure
    person = Person


def test_using_subtype_valid():
    op = OldPerson(children=1, num=1, ssid="aaa", name="dan")
    t = Trade(tradable="GOOG", person=op)
    assert t.person.name == "dan"


def test_using_subtype_valid_str():
    op = OldPerson(children=1, num=1, ssid="aaa")
    t = Trade(tradable="GOOG", person=op)
    assert (
        str(t)
        == "<Instance of Trade. Properties: person = <Instance of OldPerson. Properties: children = 1, num = 1, ssid = 'aaa'>, tradable = 'GOOG'>"
    )


def test_invalid_update_err():
    p = Person(ssid="aaa", name="dan")
    t = Trade(tradable="GOOG", person=p)
    with raises(TypeError) as excinfo:
        t.person = "danny"
    assert (
        "person: Expected <Structure: Person. Properties: "
        "foo = <Structure. Properties: a = <String>, b = <Structure. Properties: c = <Number. Properties: minimum = 10>, d = <Number. Properties: maximum = 10>>>, "
        "name = <String. Properties: maxLength = 8, pattern = '[A-Za-z]+$'>, "
        "num = <Integer. Properties: exclusiveMaximum = False, maximum = 30, minimum = 10, multiplesOf = 'dd'>, "
        "ssid = <String. Properties: minLength = 3, pattern = '[A-Za-z]+$'>>"
        in str(excinfo.value)
    )


def test_valid_update_of_property():
    p = Person(ssid="aaa", name="dan")
    t = Trade(tradable="GOOG", person=p)
    p.num = 30
    assert t.person.num == 30
    assert t.person == Person(ssid="aaa", name="dan", num=30)


def test_str_of_Trade():
    assert (
        str(Trade)
        == "<Structure: Trade. Properties: person = <ClassReference: Person>, tradable = <String>>"
    )


def test_str_of_Trade_instance():
    p = Person(ssid="aaa", name="dan")
    t = Trade(tradable="GOOG", person=p)
    assert (
        str(t)
        == "<Instance of Trade. Properties: person = <Instance of Person. Properties: name = 'dan', ssid = 'aaa'>, tradable = 'GOOG'>"
    )


def test_str_of_Person_instance_missing_fiels():
    assert str(Person(ssid="aaa")) == "<Instance of Person. Properties: ssid = 'aaa'>"


def test_several_layers():
    class A(Structure):
        i = Integer()

    class B(Structure):
        e = Enum(values=["X", "Y", "Z"])
        a = A

    class C(Structure):
        s = SizedString(maxlen=10)
        b = B

    a = A(i=5)
    b = B(e="X", a=a)
    c = C(b=b, s="x")

    assert c.b.a.i == 5
    assert (
        str(c) == "<Instance of C. Properties: b = <Instance of B. Properties: "
        "a = <Instance of A. Properties: i = 5>, e = 'X'>, s = 'x'>"
    )


def test_several_layers_variation():
    class A(Structure):
        i = Integer()

    class B(Structure):
        e = Enum(values=["X", "Y", "Z"])
        a = ClassReference(A)

    class C(Structure):
        s = SizedString(maxlen=10)
        b = ClassReference(B)

    a = A(i=5)
    b = B(e="X", a=a)
    c = C(b=b, s="x")

    assert c.b.a.i == 5
    assert (
        str(c) == "<Instance of C. Properties: b = <Instance of B. Properties: "
        "a = <Instance of A. Properties: i = 5>, e = 'X'>, s = 'x'>"
    )


def test_multiple_inheritance():
    assert Example(a=5, ssid="aaa", b="x", num=3, children=1).a == 5


def test_multiple_inheritance_missing_inherited_field_err():
    with raises(TypeError) as excinfo:
        assert Example(a=5, ssid="aaa", b="x", children=1)
        assert "missing a required argument: 'num'" in str(excinfo.value)
