import json
from datetime import datetime

import re

from typedpy import TypedField
from typedpy.fields import String

EmailAddress = String(pattern="(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


class JSONString(String):
    def __set__(self, instance, value):
        json.loads(value)
        super().__set__(instance, value)


class IPV4(String):
    _ipv4_re = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")

    def __set__(self, instance, value):
        if not IPV4._ipv4_re.match(value):
            return False
        if not all(0 <= int(component) <= 255 for component in value.split(".")):
            raise ValueError("{}: wrong format for IPV4".format(self._name))
        super().__set__(instance, value)


class HostName(String):
    _host_name_re = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\.\-]{1,255}$")

    def __set__(self, instance, value):
        if not HostName._host_name_re.match(value):
            raise ValueError("{}: wrong format for hostname".format(self._name))
        components = value.split(".")
        for component in components:
            if len(component) > 63:
                raise ValueError("{}: wrong format for hostname".format(self._name))
        super().__set__(instance, value)


class DateString(TypedField):
    """
    A string field of the format '%Y-%m-%d' that can be converted to a date
    """
    _ty = str

    def __set__(self, instance, value):
        super().__set__(instance, value)
        try:
            datetime.strptime(value, '%Y-%m-%d')
        except ValueError as ex:
            raise ValueError("{}: {}".format(self._name, ex.args[0]))


class TimeString(TypedField):
    """
    A string field of the format '%H:%M:%S' that can be converted to a time
    """
    _ty = str

    def __set__(self, instance, value):
        super().__set__(instance, value)
        try:
            datetime.strptime(instance, "%H:%M:%S")
        except ValueError as ex:
            raise ValueError("{}:  {}".format(self._name, ex.args[0]))
