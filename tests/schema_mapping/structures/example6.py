from typedpy import Structure, mappers


class Example6(Structure):
    a: int
    ssss_ttt: str

    _serialization_mapper = [{"a": "bb_cc"}, mappers.TO_CAMELCASE, {"ssssTtt": "x"}]
