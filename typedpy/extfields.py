import json
from datetime import datetime, date
import re

from typedpy import Field
from typedpy.fields import TypedField, SerializableField
from typedpy.fields import String

EmailAddress = String(pattern=r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9]+$)")


class JSONString(String):
    """
      A string of a valid JSON
    """

    def __set__(self, instance, value):
        json.loads(value)
        super().__set__(instance, value)


class IPV4(String):
    """
      A string field of a valid IP version 4
    """
    _ipv4_re = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")

    def __set__(self, instance, value):
        if IPV4._ipv4_re.match(value) and \
                all(0 <= int(component) <= 255 for component in value.split(".")):
            super().__set__(instance, value)
        else:
            raise ValueError("{}: wrong format for IP version 4".format(self._name))


class HostName(String):
    """
      A string field of a valid host name
    """

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

    Arguments:
          date_format(str): optional
              an alternative date format

    """
    _ty = str

    def __init__(self, *args, date_format="%Y-%m-%d", **kwargs):
        self._format = date_format
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        super().__set__(instance, value)
        try:
            datetime.strptime(value, self._format)
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
            datetime.strptime(value, "%H:%M:%S")
        except ValueError as ex:
            raise ValueError("{}:  {}".format(self._name, ex.args[0]))


class DateField(Field, SerializableField):
    def __init__(self, *args, date_format="%Y-%m-%d", **kwargs):
        self._date_format = date_format
        super().__init__(*args, **kwargs)

    def serialize(self, value):
        return value.strftime(self._date_format)

    def deserialize(self, value):
        return datetime.strptime(value, self._date_format).date()

    def __set__(self, instance, value):
        if isinstance(value, str):
            as_date = datetime.strptime(value, self._date_format).date()
            super().__set__(instance, as_date)
        elif isinstance(value, date):
            super().__set__(instance, value)
        elif isinstance(value, datetime):
            sum().__set__(instance, value.date())
        else:
            raise TypeError("{}: expected date, datetime, or str".format(self._name))
