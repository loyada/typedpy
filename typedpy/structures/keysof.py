import enum

from .structures import StructMeta


def keys_of(*enum_classes):
    """
    A class decorator that ensures the class fields include all the names of the enum values of the given enum classes.
     If not, the class definition throws a TypeError.
    For example:

    .. code-block:: python

        class Role(enum.Enum):
            admin = auto()
            manager = auto()
            sales = auto()
            engineer = auto()
            driver = auto()


       @keys_of(Role)
       class SalaryRules(Structure):
            admin: Range
            manager: Range
            sales: Range

            policies: list[Policy]

       # This class definiton will throw the following exception:
       # TypeError: SalaryRules: missing fields: driver, engineer

    """
    for clazz in enum_classes:
        if not issubclass(clazz, enum.Enum):
            raise TypeError(f"keys_of requires enum classes as parameters; Got {clazz}")

    def wrapper(clazz: StructMeta):
        field_names = set(clazz.get_all_fields_by_name().keys())
        expected_field_names = set()
        for c in enum_classes:
            expected_field_names |= set(e.name for e in c)
        if not expected_field_names <= field_names:
            missing_fields = sorted(expected_field_names - field_names)
            raise TypeError(
                f"{clazz.__name__}: missing fields: {', '.join(missing_fields)}"
            )
        return clazz

    return wrapper
