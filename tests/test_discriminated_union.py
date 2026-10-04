import enum
from typing import Union

import pytest

from typedpy import (
    AbstractStructure,
    Constant,
    Deserializer,
    DiscriminatedUnion,
    Enum,
    FastSerializable,
    Serializer,
    Structure,
    deserialize_structure,
    serialize,
)
from typedpy.json_schema import structure_to_schema


class EventSubject(enum.Enum):
    foo = 1
    bar = 2
    baz = 3


class Event(AbstractStructure):
    subject: Enum[EventSubject]
    name: str


class FooEvent(Event):
    subject = Constant(EventSubject.foo)
    extra: int


class BarEvent(Event):
    subject = Constant(EventSubject.bar)


class Holder(Structure):
    event = DiscriminatedUnion(Event, by=Event.subject)


def test_construct_and_access():
    holder = Holder(event=FooEvent(name="x", extra=5))
    assert isinstance(holder.event, FooEvent)
    assert holder.event.subject is EventSubject.foo
    assert holder.event.extra == 5

    holder2 = Holder(event=BarEvent(name="y"))
    assert isinstance(holder2.event, BarEvent)


def test_rejects_non_variant_value():
    with pytest.raises(TypeError) as excinfo:
        Holder(event="not an event")
    assert "FooEvent" in str(excinfo.value) or "BarEvent" in str(excinfo.value)

    with pytest.raises(TypeError):
        Holder(event=Event(name="x", subject=EventSubject.foo))


def test_by_must_be_a_field():
    with pytest.raises(TypeError) as excinfo:
        DiscriminatedUnion(Event, by="subject")
    assert "'by' must be a field (e.g. Event" in str(excinfo.value)


def test_by_rejects_a_variants_constant():
    # FooEvent.subject is a Constant, not a Field (Constant has no descriptor
    # protocol), so this is rejected by the same check as any other non-field value.
    with pytest.raises(TypeError) as excinfo:
        DiscriminatedUnion(Event, by=FooEvent.subject)
    assert "'by' must be a field (e.g. Event" in str(excinfo.value)


def test_by_rejects_a_field_from_the_wrong_class():
    class Other(Structure):
        subject: Enum[EventSubject]

    with pytest.raises(TypeError) as excinfo:
        DiscriminatedUnion(Event, by=Other.subject)
    assert "must be Event's own field" in str(excinfo.value)


def test_base_cls_must_be_a_structure():
    with pytest.raises(TypeError) as excinfo:
        DiscriminatedUnion(int, by=Event.subject)
    assert "expected a Structure subclass" in str(excinfo.value)


def test_missing_constant_raises():
    class Base(AbstractStructure):
        subject: Enum[EventSubject]

    class GoodVariant(Base):
        subject = Constant(EventSubject.foo)

    class BadVariant(Base):  # forgot to redeclare subject as a Constant
        pass

    field = DiscriminatedUnion(Base, by=Base.subject)
    with pytest.raises(TypeError) as excinfo:
        field._ensure_variants()
    assert "BadVariant" in str(excinfo.value)
    assert "does not define subject as a Constant" in str(excinfo.value)


def test_duplicate_tag_raises():
    class Base(AbstractStructure):
        subject: Enum[EventSubject]

    class VariantA(Base):
        subject = Constant(EventSubject.foo)

    class VariantB(Base):
        subject = Constant(EventSubject.foo)

    field = DiscriminatedUnion(Base, by=Base.subject)
    with pytest.raises(TypeError) as excinfo:
        field._ensure_variants()
    assert "duplicate discriminator value" in str(excinfo.value)
    assert "VariantA" in str(excinfo.value) and "VariantB" in str(excinfo.value)


def test_no_variants_raises():
    class Lonely(AbstractStructure):
        subject: Enum[EventSubject]

    field = DiscriminatedUnion(Lonely, by=Lonely.subject)
    with pytest.raises(TypeError) as excinfo:
        field._ensure_variants()
    assert "no variants found" in str(excinfo.value)


def test_variants_discovered_lazily_after_definition():
    class Base(AbstractStructure):
        subject: Enum[EventSubject]

    field = DiscriminatedUnion(Base, by=Base.subject)

    class LateVariant(Base):
        subject = Constant(EventSubject.foo)

    # the table is only built on first use, so LateVariant (defined after the
    # DiscriminatedUnion field itself) is still found.
    variants = field._ensure_variants()
    assert variants == {EventSubject.foo: LateVariant}


def test_variant_defined_after_the_table_is_first_cached_is_still_found_on_miss():
    class Base(AbstractStructure):
        subject: Enum[EventSubject]

    class FooVariant(Base):
        subject = Constant(EventSubject.foo)

    class Holder2(Structure):
        event = DiscriminatedUnion(Base, by=Base.subject)

    # force the table to be built and cached now, before BarVariant exists
    holder = Holder2(event=FooVariant())
    field = Holder2.event
    assert field._ensure_variants() == {EventSubject.foo: FooVariant}

    class BarVariant(Base):
        subject = Constant(EventSubject.bar)

    # a stale read of the cache doesn't see BarVariant yet
    assert BarVariant not in field._ensure_variants().values()

    # but deserializing a "bar" value triggers a refresh and succeeds
    holder2 = deserialize_structure(Holder2, {"event": {"subject": "bar"}})
    assert isinstance(holder2.event, BarVariant)

    # and so does direct assignment of an instance of the new variant
    holder.event = BarVariant()
    assert isinstance(holder.event, BarVariant)


def test_subclass_of_a_tagged_variant_inherits_its_tag():
    class Base(AbstractStructure):
        subject: Enum[EventSubject]

    class FooVariant(Base):
        subject = Constant(EventSubject.foo)

    class SpecialFooVariant(FooVariant):
        extra: int

    field = DiscriminatedUnion(Base, by=Base.subject)
    variants = field._ensure_variants()
    # SpecialFooVariant isn't registered as its own variant -- it shares
    # FooVariant's tag, so a "foo"-tagged value deserializes as FooVariant
    assert variants == {EventSubject.foo: FooVariant}

    class Holder2(Structure):
        event = DiscriminatedUnion(Base, by=Base.subject)

    # a SpecialFooVariant instance is still accepted (it IS a FooVariant)
    holder = Holder2(event=SpecialFooVariant(extra=1))
    assert isinstance(holder.event, SpecialFooVariant)


def test_serialize_slow_path():
    holder = Holder(event=FooEvent(name="x", extra=5))
    assert serialize(holder) == {"event": {"subject": "foo", "name": "x", "extra": 5}}
    assert Serializer(holder).serialize() == {
        "event": {"subject": "foo", "name": "x", "extra": 5}
    }

    holder2 = Holder(event=BarEvent(name="y"))
    assert serialize(holder2) == {"event": {"subject": "bar", "name": "y"}}


def test_deserialize_slow_path():
    holder = deserialize_structure(
        Holder, {"event": {"subject": "foo", "name": "x", "extra": 5}}
    )
    assert isinstance(holder.event, FooEvent)
    assert holder.event == FooEvent(name="x", extra=5)

    holder2 = Deserializer(Holder).deserialize(
        {"event": {"subject": "bar", "name": "y"}}
    )
    assert isinstance(holder2.event, BarEvent)


def test_deserialize_unmatched_discriminator():
    with pytest.raises(ValueError) as excinfo:
        deserialize_structure(Holder, {"event": {"subject": "baz", "name": "x"}})
    assert "subject: got" in str(excinfo.value)
    assert "EventSubject.baz" in str(excinfo.value)


def test_deserialize_respects_camel_case():
    class CcEvent(AbstractStructure):
        subject: Enum[EventSubject]
        my_name: str

    class CcFooEvent(CcEvent):
        subject = Constant(EventSubject.foo)

    class CcHolder(Structure):
        my_event = DiscriminatedUnion(CcEvent, by=CcEvent.subject)

    holder = deserialize_structure(
        CcHolder,
        {"myEvent": {"subject": "foo", "myName": "x"}},
        camel_case_convert=True,
    )
    assert isinstance(holder.my_event, CcFooEvent)
    assert holder.my_event.my_name == "x"


class FastEvent(Structure, FastSerializable):
    subject: Enum[EventSubject]
    name: str


class FastFooEvent(FastEvent):
    subject = Constant(EventSubject.foo)
    extra: int


class FastBarEvent(FastEvent):
    subject = Constant(EventSubject.bar)


class FastHolder(Structure, FastSerializable):
    event = DiscriminatedUnion(FastEvent, by=FastEvent.subject)


def test_fast_serialization_dispatches_by_runtime_type():
    foo_holder = FastHolder(event=FastFooEvent(name="x", extra=5))
    assert foo_holder.serialize() == {
        "event": {"subject": "foo", "name": "x", "extra": 5}
    }

    bar_holder = FastHolder(event=FastBarEvent(name="y"))
    assert bar_holder.serialize() == {"event": {"subject": "bar", "name": "y"}}


def test_json_schema_oneof_with_enum_restriction():
    schema, definitions = structure_to_schema(Holder, {})
    assert schema["properties"]["event"] == {
        "oneOf": [
            {"$ref": "#/definitions/FooEvent"},
            {"$ref": "#/definitions/BarEvent"},
        ]
    }
    assert definitions["FooEvent"]["properties"]["subject"] == {"enum": ["foo"]}
    assert definitions["BarEvent"]["properties"]["subject"] == {"enum": ["bar"]}


# --- explicit Union[...] mode: no shared base class, each variant stands alone ---


class Circle(Structure):
    type = Constant("circle")
    radius: int


class Square(Structure):
    type = Constant("square")
    side: int


class Canvas(Structure):
    shape = DiscriminatedUnion(Union[Circle, Square], by=Circle.type)


def test_explicit_union_construct_and_access():
    canvas = Canvas(shape=Circle(radius=5))
    assert isinstance(canvas.shape, Circle)

    canvas2 = Canvas(shape=Square(side=3))
    assert isinstance(canvas2.shape, Square)


def test_explicit_union_rejects_non_variant_value():
    with pytest.raises(TypeError):
        Canvas(shape="not a shape")


def test_explicit_union_requires_structure_subclasses():
    with pytest.raises(TypeError) as excinfo:
        DiscriminatedUnion(Union[Circle, int], by=Circle.type)
    assert "expected a Union of Structure subclasses" in str(excinfo.value)


def test_explicit_union_by_can_be_a_constant_on_one_of_the_variants():
    # Circle.type is itself a Constant (no shared base class defines a plain
    # version of the field) -- used only to name the discriminator field.
    field = DiscriminatedUnion(Union[Circle, Square], by=Circle.type)
    assert field._ensure_variants() == {"circle": Circle, "square": Square}


def test_explicit_union_by_must_belong_to_one_of_the_variants():
    class Other(Structure):
        name: str

    with pytest.raises(TypeError) as excinfo:
        DiscriminatedUnion(Union[Circle, Square], by=Other.name)
    assert "not defined directly on any of: Circle, Square" in str(excinfo.value)


def test_explicit_union_missing_constant_raises():
    class Triangle(Structure):
        sides: int  # forgot to define 'type' as a Constant

    with pytest.raises(TypeError) as excinfo:
        DiscriminatedUnion(Union[Circle, Triangle], by=Circle.type)._ensure_variants()
    assert "Triangle does not define type as a Constant" in str(excinfo.value)


def test_explicit_union_duplicate_tag_raises():
    class Hexagon(Structure):
        type = Constant("circle")  # duplicate tag

    with pytest.raises(TypeError) as excinfo:
        DiscriminatedUnion(Union[Circle, Hexagon], by=Circle.type)._ensure_variants()
    assert "duplicate discriminator value" in str(excinfo.value)


def test_explicit_union_serialize_and_deserialize():
    canvas = Canvas(shape=Circle(radius=5))
    assert serialize(canvas) == {"shape": {"type": "circle", "radius": 5}}

    canvas2 = deserialize_structure(Canvas, {"shape": {"type": "square", "side": 3}})
    assert isinstance(canvas2.shape, Square)
    assert canvas2.shape.side == 3


class FastCircle(Structure, FastSerializable):
    type = Constant("circle")
    radius: int


class FastSquare(Structure, FastSerializable):
    type = Constant("square")
    side: int


class FastCanvas(Structure, FastSerializable):
    shape = DiscriminatedUnion(Union[FastCircle, FastSquare], by=FastCircle.type)


def test_explicit_union_fast_serialization():
    canvas = FastCanvas(shape=FastCircle(radius=5))
    assert canvas.serialize() == {"shape": {"type": "circle", "radius": 5}}

    canvas2 = FastCanvas(shape=FastSquare(side=3))
    assert canvas2.serialize() == {"shape": {"type": "square", "side": 3}}


def test_explicit_union_json_schema():
    schema, definitions = structure_to_schema(Canvas, {})
    assert schema["properties"]["shape"] == {
        "oneOf": [
            {"$ref": "#/definitions/Circle"},
            {"$ref": "#/definitions/Square"},
        ]
    }
    assert definitions["Circle"]["properties"]["type"] == {"enum": ["circle"]}
    assert definitions["Square"]["properties"]["type"] == {"enum": ["square"]}
