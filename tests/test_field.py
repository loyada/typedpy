from datetime import date, datetime

from pytest import raises

from typedpy import Boolean, unique, String, Structure


def test_unique_field_violation(uniqueness_enabled):
    @unique
    class SSID(String):
        pass

    class Person(Structure):
        ssid: SSID
        name: String

    Person(ssid="1234", name="john")
    person_1 = Person(
        ssid="1234", name="john"
    )  # OK - structure is equal to previous one
    Person(ssid="2345", name="Jeff")  # OK - value of ssid is different
    with raises(ValueError) as excinfo:
        Person(ssid="1234", name="Jack")
    assert (
        "Instance copy of field ssid in Person, which is defined as unique. Instance is '1234'"
        in str(excinfo.value)
    )

    with raises(ValueError) as excinfo:
        person_1.name = "Joe"
    assert (
        "Instance copy of field ssid in Person, which is defined as unique. Instance is '1234'"
        in str(excinfo.value)
    )


def test_unique_field_violation_by_update(uniqueness_enabled):
    @unique
    class SSID(String):
        pass

    class Person(Structure):
        ssid: SSID
        name: String

    Person(ssid="1234", name="john")
    person_1 = Person(
        ssid="1234", name="john"
    )  # OK - structure is equal to previous one

    with raises(ValueError) as excinfo:
        person_1.name = "Joe"
    assert (
        "Instance copy of field ssid in Person, which is defined as unique. Instance is '1234'"
        in str(excinfo.value)
    )


def test_unique_field_multiple_structures_are_allowed_to_have_same_values():
    @unique
    class SSID(String):
        pass

    class Person(Structure):
        ssid: SSID
        name: String

    class Employee(Structure):
        ssid: SSID
        name: String

    Person(ssid="1234", name="john")
    Employee(ssid="1234", name="Jack")


def test_unique_field_using_parameter_violation(uniqueness_enabled):
    class SSID(String):
        pass

    class Person(Structure):
        ssid: SSID(is_unique=True)
        name: String

    Person(ssid="1234", name="john")
    Person(ssid="1234", name="john")  # OK - structure is equal to previous one
    Person(ssid="2345", name="Jeff")
    with raises(ValueError) as excinfo:
        Person(ssid="1234", name="Jack")
    assert (
        "Instance copy of field ssid in Person, which is defined as unique. Instance is '1234'"
        in str(excinfo.value)
    )


def test_boolean_string_assignment():
    class Foo(Structure):
        a: Boolean

    foo = Foo(a="False")
    assert foo.a is False
    foo.a = "True"
    assert foo.a is True


def test_datetime():
    class Foo(Structure):
        d: date
        t: datetime

    now = datetime.now()
    foo = Foo(d=now.date(), t=now)
    assert foo.d == now.date()
    assert foo.t == now
    foo.d = str(foo.d)
    assert foo.d == now.date()
    with raises(TypeError) as excinfo:
        foo.t = 123
