from datetime import datetime
import json

from pytest import raises

from typedpy import String, Structure, ImmutableField, DateString, TimeString, EmailAddress, HostName, IPV4, JSONString


class ImmutableString(String, ImmutableField): pass

class B(Structure):
    s = String(maxLength=5, minLength=2)
    a = ImmutableString()


def test_max_length_violation_err():
    with raises(ValueError) as excinfo:
        B(s = 'abcdef', a='')
    assert "s: Expected a maxmimum length of 5" in str(excinfo.value)


def test_min_length_violation_err():
    with raises(ValueError) as excinfo:
        B(s = 'a', a='')
    assert "s: Expected a minimum length of 2" in str(excinfo.value)


def test_immutable_err():
    b = B(s='sss', a='asd')
    with raises(ValueError) as excinfo:
        b.a = 'dd'
    assert "a: Field is immutable" in str(excinfo.value)


def test_date_err():
    class Example(Structure):
        d = DateString
    with raises(ValueError) as excinfo:
         Example(d='2017-99-99')
    assert "d: time data '2017-99-99' does not match format" in str(excinfo.value)

def test_date_valid():
    class Example(Structure):
        d = DateString
    e = Example(d='2017-8-9')
    assert datetime.strptime(e.d, '%Y-%m-%d').month==8


def test_time_err():
    class Example(Structure):
        t = TimeString
    with raises(ValueError) as excinfo:
        Example(t='20:1015')
    assert "t:  time data '20:1015' does not match format '%H:%M:%S'" in str(excinfo.value)


def test_time_valid():
    class Example(Structure):
        t = TimeString
    e = Example(t='20:10:15')
    assert datetime.strptime(e.t, '%H:%M:%S').hour==20


def test_email_err():
    class Example(Structure):
        email = EmailAddress
    with raises(ValueError) as excinfo:
        Example(email='asdnsa@dsads.sds.')
    assert "email: Does not match regular expression" in str(excinfo.value)


def test_email_valid():
    class Example(Structure):
        email = EmailAddress
    Example(email='abc@com.ddd').email=='abc@com.ddd'


def test_hostname_err():
    class Example(Structure):
        host = HostName
    with raises(ValueError) as excinfo:
        Example(host='aaa bbb')
    assert "host: wrong format for hostname" in str(excinfo.value)


def test_hostname_valid():
    class Example(Structure):
        host = HostName
    Example(host='com.ddd.dasdasdsadasdasda').host=='com.ddd.dasdasdsadasdasda'

def test_ipv4_err():
    class Example(Structure):
        ip = IPV4
    with raises(ValueError) as excinfo:
        Example(ip='2312.2222.223233')
    assert "ip: wrong format for IP version 4" in str(excinfo.value)


def test_hostname_valid():
    class Example(Structure):
        ip = IPV4
    Example(ip='212.22.33.192').ip.split('.')==['212','22', '33', '192']


def test_JSONString_err():
    class Example(Structure):
        j = JSONString
    with raises(ValueError) as excinfo:
        Example(j='[1,2,3')


def test_JSONString_valid():
    class Example(Structure):
        j = JSONString
    assert json.loads(Example(j='[1,2,3]').j) == [1,2,3]
