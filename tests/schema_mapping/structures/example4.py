from typedpy import Structure, mappers


class Example4(Structure):
    first_name: str
    last_name: str
    social_security: str
    age_years: int

    _serialization_mapper = mappers.TO_CAMELCASE

