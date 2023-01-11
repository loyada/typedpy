from typedpy import Structure, Serializer
from typedpy import ExceptionField


def test_serialize():
    class Foo(Structure):
        e: ExceptionField
        _additionalProperties = False

    try:
        raise ValueError("my exception")
    except ValueError as exc:
        foo = Foo(e=exc)
        serialized = Serializer(foo).serialize(compact=True)
        assert serialized == "ValueError"
