"""
Additional types of fields: datefield, datetime, timestring, DateString,
Hostname, etc.
"""
import json
from datetime import datetime, date
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
                "{}: Got {}; wrong format for IP version 4".format(
                    self._name, wrap_val(value)
                )
            )


class HostName(String):
    """
    A string field of a valid host name
    """

    _host_name_re = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\.\-]{1,255}$")

    def __set__(self, instance, value):
        if not HostName._host_name_re.match(value):
            raise ValueError(
                "{}: Got {}; wrong format for hostname".format(
                    self._name, wrap_val(value)
                )
            )
        components = value.split(".")
        for component in components:
            if len(component) > 63:
                raise ValueError(
                    "{}: Got {}; wrong format for hostname".format(
                        self._name, wrap_val(value)
                    )
                )
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
            raise ValueError(
                "{}: Got {}; {}".format(self._name, wrap_val(value), ex.args[0])
            ) from ex


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
                "{}: Got {}; {}".format(self._name, wrap_val(value), ex.args[0])
            ) from ex


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
            raise ValueError(
                "{}: Got {}; {}".format(self._name, wrap_val(value), str(ex))
            ) from ex

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
                "{}: Got {}; Expected date, datetime, or str".format(
                    self._name, wrap_val(value)
                )
            )


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
            return datetime.strptime(value, self._datetime_format)
        except ValueError as ex:
            raise ValueError(
                "{}: Got {}; {}".format(self._name, wrap_val(value), str(ex))
            ) from ex

    def __set__(self, instance, value):
        if isinstance(value, str):
            as_datetime = self.deserialize(value)
            super().__set__(instance, as_datetime)
        elif isinstance(value, datetime):
            super().__set__(instance, value)
        else:
            raise TypeError(
                "{}: Got {}; Expected datetime or str".format(
                    self._name, wrap_val(value)
                )
            )
