from typedpy.commons import wrap_val
from typedpy.structures import Field, FieldMeta, NoneField, ClassReference, TypedField
from .fields import _map_to_field


class _JSONSchemaDraft4ReuseMeta(FieldMeta):
    def __getitem__(cls, item):
        def validate_and_get_field(val):
            return FieldMeta.__getitem__(cls, val)

        if isinstance(item, tuple):
            fields = [validate_and_get_field(it) for it in item]
            return cls(fields)  # pylint: disable=E1120, E1123
        return cls([validate_and_get_field(item)])  # pylint: disable=E1120, E1123


def _str_for_multioption_field(instance):
    name = instance.__class__.__name__
    if instance.get_fields():
        fields_st = ", ".join([str(field) for field in instance.get_fields()])
        propst = f" [{fields_st}]"
    else:
        propst = ""
    return f"<{name}{propst}>"


class MultiFieldWrapper:
    """
    An abstract base class for AllOf, AnyOf, OneOf, etc.
    It provides flexibility in reading the "fields" argument.
    """

    def __init__(self, *arg, fields, **kwargs):
        if isinstance(fields, list):
            self._fields = []
            for item in fields:
                self._fields.append(_map_to_field(item))
        else:
            raise TypeError("Expected a Field class or instance")
        super().__init__(*arg, **kwargs)

    def get_fields(self):
        return self._fields


class AllOf(MultiFieldWrapper, Field, metaclass=_JSONSchemaDraft4ReuseMeta):
    """
    Content must adhere to all requirements in the fields arguments.
    Arguments:

        fields( `list` of :class:`Field`): optional
        the content should match all of the fields in the list

    Example:

    .. code-block:: python

        AllOf[Number(maximum=20, minimum=-10), Integer, Positive]

    """

    def __init__(self, fields):
        super().__init__(fields=fields)

    def __set__(self, instance, value):
        for field in self.get_fields():
            setattr(field, "_name", self._name)
            field.__set__(instance, value)
        super().__set__(instance, value)

    def __str__(self):
        return _str_for_multioption_field(self)

    def serialize(self, value):
        field = self.get_fields()[0]
        return field.serialize(value)


def _get_type_name(field):
    if isinstance(field, ClassReference):
        return field._ty.__name__
    clz = field.__class__
    if clz is NoneField:
        return "None"
    if isinstance(field, TypedField):
        return clz._ty.__name__
    return clz.__name__


class AnyOf(MultiFieldWrapper, Field, metaclass=_JSONSchemaDraft4ReuseMeta):
    """
    Content must adhere to one or more of the requirements in the fields arguments.
    Arguments:

        fields( `list` of :class:`Field`): optional
        the content should match at least one of the fields in the list

    Example:

    .. code-block:: python

       AnyOf[Number(maximum=20, minimum=-10), Integer, Positive, String]

    """

    def __init__(self, fields):
        super().__init__(fields=fields)
        if self.get_fields():
            for f in self.get_fields():
                if isinstance(f, NoneField):
                    self._is_optional = True
                else:
                    self._not_nonefield = f
        else:
            raise TypeError("AnyOf definition must include at least one field option")

    def __set__(self, instance, value):
        if getattr(instance, "_trust_supplied_values", False):
            super().__set__(instance, value)
            return
        matched = False
        for field in self.get_fields():
            setattr(field, "_name", self._name)
            try:
                field.__set__(instance, value)
                matched = True
                break
            except TypeError:
                pass
            except ValueError:
                pass
        if not matched:
            prefix = f"{self._name}: " if self._name else ""
            valid_type_names = ", ".join([_get_type_name(f) for f in self.get_fields()])
            raise ValueError(
                f"{prefix}{wrap_val(value)} of type {value.__class__.__name__} did not match"
                f" any field option. Valid types are: {valid_type_names}."
            )
        super().__set__(instance, getattr(instance, self._name))

    def __str__(self):
        return _str_for_multioption_field(self)

    def serialize(self, value):
        return None if value is None else self._not_nonefield.serialize(value)


class OneOf(MultiFieldWrapper, Field, metaclass=_JSONSchemaDraft4ReuseMeta):
    """
    Content must adhere to one, and only one, of the requirements in the fields arguments.
    Arguments:

        fields( `list` of :class:`Field`): optional
        the content should match one, and only one, of the fields in the list

    Example:

    .. code-block:: python

        OneOf[Number(maximum=20, minimum=-10), Integer, Positive, String]

    """

    def __init__(self, fields):
        super().__init__(fields=fields)

    def __set__(self, instance, value):
        matched = 0
        for field in self.get_fields():
            setattr(field, "_name", self._name)
            try:
                field.__set__(instance, value)
                matched += 1
            except TypeError:
                pass
            except ValueError:
                pass
        if not matched:
            valid_type_names = ", ".join([_get_type_name(f) for f in self.get_fields()])
            prefix = f"{self._name}: " if self._name else ""
            raise ValueError(
                f"{prefix}{wrap_val(value)} of type {value.__class__.__name__} did not match"
                f" any field option. Valid types are: {valid_type_names}."
            )
        if matched > 1:
            prefix = f"{self._name}: " if self._name else ""
            raise ValueError(
                f"{prefix}: Got {wrap_val(value)}; Matched more than one field option"
            )
        super().__set__(instance, value)

    def __str__(self):
        return _str_for_multioption_field(self)

    def serialize(self, value):
        raise TypeError("Not FastSerializable")


class NotField(MultiFieldWrapper, Field, metaclass=_JSONSchemaDraft4ReuseMeta):
    """
    Content *must not* adhere to any of the requirements in the fields arguments.
    Arguments:

        fields( `list` of :class:`Field`): optional
            the content must not match any of the fields in the lists

    Examples:

    .. code-block:: python

        NotField([Number(multiplesOf=5, maximum=20, minimum=-10), String])
        NotField[Positive]

    """

    def __init__(self, fields):
        super().__init__(fields=fields)

    def __set__(self, instance, value):
        for field in self.get_fields():
            setattr(field, "_name", self._name)
            try:
                field.__set__(instance, value)
            except TypeError:
                pass
            except ValueError:
                pass
            else:
                raise ValueError(
                    f"{self._name}: Got {wrap_val(value)}; Expected not to match any field definition"
                )
        super().__set__(instance, value)

    def __str__(self):
        return _str_for_multioption_field(self)
