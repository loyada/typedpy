"""
Additional types of fields: datefield, datetime, timestring, DateString,
Hostname, etc.
"""
import json
from datetime import datetime, date, time
import re

from typedpy.commons import wrap_val
from typedpy.structures import TypedField
from typedpy.fields import SerializableField, String

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
        if IPV4._ipv4_re.match(value) and all(
            0 <= int(component) <= 255 for component in value.split(".")
        ):
            super().__set__(instance, value)
        else:
            raise ValueError(
                f"{self._name}: Got {wrap_val(value)}; wrong format for IP version 4"
            )

    def to_json_schema(self) -> dict:
        return {"type": "string", "format": "ipv4"}

    @classmethod
    def from_json_schema(cls, schema: dict):
        return "IPV4()" if schema == {"type": "string", "format": "ipv4"} else None


class HostName(String):
    """
    A string field of a valid host name
    """

    _host_name_re = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\.\-]{1,255}$")

    def __set__(self, instance, value):
        if not HostName._host_name_re.match(value):
            raise ValueError(
                f"{self._name}: Got {wrap_val(value)}; wrong format for hostname"
            )
        components = value.split(".")
        for component in components:
            if len(component) > 63:
                raise ValueError(
                    f"{self._name}: Got {wrap_val(value)}; wrong format for hostname"
                )
        super().__set__(instance, value)

    def to_json_schema(self) -> dict:
        return {"type": "string", "format": "hostname"}

    @classmethod
    def from_json_schema(cls, schema: dict):
        return (
            "HostName()" if schema == {"type": "string", "format": "hostname"} else None
        )


class DateString(String):
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
            raise ValueError(
                f"{self._name}: Got {wrap_val(value)}; {ex.args[0]}"
            ) from ex

    def to_json_schema(self) -> dict:
        return {"type": "string", "format": "date"}

    @classmethod
    def from_json_schema(cls, schema: dict):
        return (
            "DateString()" if schema == {"type": "string", "format": "date"} else None
        )


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
            raise ValueError(
                f"{self._name}: Got {wrap_val(value)}; {ex.args[0]}"
            ) from ex

    def to_json_schema(self) -> dict:
        return {"type": "string", "format": "time"}

    @classmethod
    def from_json_schema(cls, schema: dict):
        return (
            "TimeString()" if schema == {"type": "string", "format": "time"} else None
        )

    def serialize(self, value):
        return value


class DateField(SerializableField):
    """
    A datetime.date field. Can accept either a date object, or a string
    that can be converted to a date, using the date_format in the constructor.

    Arguments:
         date_format(str): optional
             The date format used to convert to/from a string. Default is '%Y-%m-%d'

    Example:

    .. code-block:: python

        class Foo(Structure):
            date = DateField

        foo(date = date.today())
        foo(date = "2020-01-31")

    This is a SerializableField, thus can be serialized/deserialized.

    """

    def __init__(self, *args, date_format="%Y-%m-%d", **kwargs):
        self._date_format = date_format
        super().__init__(*args, **kwargs)

    def serialize(self, value):
        return value.strftime(self._date_format)

    def deserialize(self, value):
        try:
            return datetime.strptime(value, self._date_format).date()
        except ValueError as ex:
            raise ValueError(f"{self._name}: Got { wrap_val(value)}; {str(ex)}") from ex

    def __set__(self, instance, value):
        if isinstance(value, str):
            as_date = self.deserialize(value)
            super().__set__(instance, as_date)
        elif isinstance(value, datetime):
            super().__set__(instance, value.date())
        elif isinstance(value, date):
            super().__set__(instance, value)
        else:
            raise TypeError(
                f"{self._name}: Got {wrap_val(value)}; Expected date, datetime, or str"
            )

    @property
    def get_type(self):
        return date

    def to_json_schema(self) -> dict:
        return {"type": "string", "format": "date"}

    @classmethod
    def from_json_schema(cls, schema: dict):
        return "DateField()" if schema == {"type": "string", "format": "date"} else None


class TimeField(SerializableField):
    def __init__(self, format_str="%H:%M:%S", **kwargs):
        self._format = format_str
        super().__init__(**kwargs)

    def __set__(self, instance, value):
        parsed_time = value if isinstance(value, time) else self.deserialize(value)
        super().__set__(instance, parsed_time)

    def serialize(self, value: time):
        return value.strftime(self._format)

    def deserialize(self, value):
        try:
            return datetime.strptime(value, self._format).time()
        except ValueError as ex:
            raise ValueError(f"{self._name}: Got {wrap_val(value)}; {str(ex)}") from ex

    @property
    def get_type(self):
        return time

    def to_json_schema(self) -> dict:
        return {"type": "string", "format": "time"}

    @classmethod
    def from_json_schema(cls, schema: dict):
        return "TimeField()" if schema == {"type": "string", "format": "time"} else None


class DateTime(SerializableField):
    """
    A datetime.datetime field. Can accept either a datetime object, or a string
    that can be converted to a date, using the date_format in the constructor.

    Arguments:
        datetime_format(str): optional
            The format used to convert to/from a string. Default is '%m/%d/%y %H:%M:%S'

    Example:

       .. code-block:: python

           class Foo(Structure):
               timestamp = DateTime

           foo(timestamp = datetime.now())
           foo(timestamp = "01/31/20 07:15:45")

    This is a SerializableField, thus can be serialized/deserialized.

    """

    def __init__(self, *args, datetime_format="%m/%d/%y %H:%M:%S", **kwargs):
        self._datetime_format = datetime_format
        super().__init__(*args, **kwargs)

    def serialize(self, value: datetime):
        return value.strftime(self._datetime_format)

    def deserialize(self, value):
        try:
            if isinstance(value, int) and 2000000000 > value > 1000000000:
                return datetime.fromtimestamp(value)
            return datetime.strptime(value, self._datetime_format)
        except ValueError as ex:
            raise ValueError(f"{self._name}: Got {wrap_val(value)}; {str(ex)}") from ex

    def __set__(self, instance, value):
        if isinstance(value, datetime):
            super().__set__(instance, value)
        elif isinstance(value, (str, int)):
            as_datetime = self.deserialize(value)
            super().__set__(instance, as_datetime)
        else:
            raise TypeError(
                f"{self._name}: Got {wrap_val(value)}; Expected datetime or str"
            )

    @property
    def get_type(self):
        return datetime
