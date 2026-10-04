import types
import typing

from typedpy.commons import Constant, wrap_val
from typedpy.structures import Field, Structure, StructMeta

_UNION_ORIGINS = tuple(
    o for o in (typing.Union, getattr(types, "UnionType", None)) if o is not None
)


def _as_explicit_variants(value):
    """
    If value is a Union (or X | Y) of two or more types, return its args as a tuple.
    Otherwise return None.
    """
    if typing.get_origin(value) in _UNION_ORIGINS:
        return typing.get_args(value)
    return None


class DiscriminatedUnion(Field):
    """
    A field that holds an instance of exactly one of several Structure subclasses
    ("variants"), where the concrete variant is determined by a discriminator field
    that is a ``Constant`` on every variant.

    There are two ways to declare the variants:

    1. As subclasses of a common base class (discovered automatically, lazily, on
       first use -- so variants defined or imported after this field is still found):

    .. code-block:: python

        class EventSubject(enum.Enum):
            foo = 1
            bar = 2

        class Event(Structure):
            subject: Enum[EventSubject]

        class FooEvent(Event):
            subject = Constant(EventSubject.foo)

        class BarEvent(Event):
            subject = Constant(EventSubject.bar)

        class Holder(Structure):
            event = DiscriminatedUnion(Event, by=Event.subject)

    2. As an explicit ``Union`` of otherwise-unrelated Structure classes, each of
       which independently defines the same-named discriminator field as a
       ``Constant``:

    .. code-block:: python

        class Foo(Structure):
            type = Constant("foo")

        class Bar(Structure):
            type = Constant("bar")

        class Holder(Structure):
            event = DiscriminatedUnion(Union[Foo, Bar], by=Foo.type)

    In both forms, ``by`` is a field object (e.g. ``Event.subject`` or ``Foo.type``),
    not a string, so that renaming the field is refactor-safe. In the explicit-Union
    form, ``by`` only needs to belong to one of the listed variants -- the others are
    expected to have their own field of the same name.
    """

    def __init__(self, base_cls_or_variants, *, by, **kwargs):
        explicit_variants = _as_explicit_variants(base_cls_or_variants)
        if explicit_variants is not None:
            for variant in explicit_variants:
                if not (
                    isinstance(variant, StructMeta) and issubclass(variant, Structure)
                ):
                    raise TypeError(
                        "DiscriminatedUnion: expected a Union of Structure subclasses; "
                        f"Got {wrap_val(variant)}"
                    )
            self._base_cls = None
            self._explicit_variants = explicit_variants
        else:
            base_cls = base_cls_or_variants
            if not (
                isinstance(base_cls, StructMeta) and issubclass(base_cls, Structure)
            ):
                raise TypeError(
                    "DiscriminatedUnion: expected a Structure subclass, or a Union of "
                    f"Structure subclasses; Got {wrap_val(base_cls)}"
                )
            self._base_cls = base_cls
            self._explicit_variants = None

        if self._explicit_variants is not None:
            # 'by' may be a Constant here (every variant, including by's own, can
            # define the discriminator directly as a Constant) -- a bare Constant
            # has no _name, so find by's attribute name and owner by identity scan
            # instead of reading by._name.
            by_owner, by_name = next(
                (
                    (variant, key)
                    for variant in self._explicit_variants
                    for key, val in variant.__dict__.items()
                    if val is by
                ),
                (None, None),
            )
            if by_owner is None:
                names = ", ".join(v.__name__ for v in self._explicit_variants)
                raise TypeError(
                    f"DiscriminatedUnion: 'by' must be one of the variants' own field "
                    f"or Constant; Got {wrap_val(by)}, which is not defined directly on "
                    f"any of: {names}"
                )
        else:
            by_name = getattr(by, "_name", None) if isinstance(by, Field) else None
            if by_name is None:
                raise TypeError(
                    "DiscriminatedUnion: 'by' must be a field (e.g. "
                    f"{base_cls_or_variants.__name__}.<field name>); Got {wrap_val(by)}"
                )
            if base_cls_or_variants.get_all_fields_by_name().get(by_name) is not by:
                raise TypeError(
                    f"DiscriminatedUnion: 'by' must be {base_cls_or_variants.__name__}'s own "
                    f"field {base_cls_or_variants.__name__}.{by_name}, not a different field "
                    "object with the same name"
                )
            by_owner = base_cls_or_variants

        self._by = by
        self._by_name = by_name
        self._by_owner = by_owner
        self._variants_by_tag = None
        super().__init__(**kwargs)

    def _description(self):
        if self._explicit_variants is not None:
            names = ", ".join(v.__name__ for v in self._explicit_variants)
            return f"DiscriminatedUnion(Union[{names}], by={self._by_name})"
        return f"DiscriminatedUnion({self._base_cls.__name__}, by={self._by_name})"

    def _discover_variants(self):
        if self._explicit_variants is not None:
            return self._discover_explicit_variants()
        return self._discover_inherited_variants()

    def _discover_explicit_variants(self):
        variant_by_tag = {}
        for variant in self._explicit_variants:
            tag_field = variant.get_all_fields_by_name().get(self._by_name)
            if not isinstance(tag_field, Constant):
                raise TypeError(
                    f"{self._description()}: {variant.__name__} does not define "
                    f"{self._by_name} as a Constant"
                )
            tag = tag_field()
            if tag in variant_by_tag:
                raise TypeError(
                    f"{self._description()}: duplicate discriminator value "
                    f"{wrap_val(tag)} used by both {variant_by_tag[tag].__name__} and "
                    f"{variant.__name__}"
                )
            variant_by_tag[tag] = variant
        return variant_by_tag

    def _discover_inherited_variants(self):
        variant_by_tag = {}

        def visit(cls):
            for sub in cls.__subclasses__():
                tag_field = sub.__dict__.get(self._by_name)
                if isinstance(tag_field, Constant):
                    tag = tag_field()
                    if tag in variant_by_tag:
                        raise TypeError(
                            f"{self._description()}: duplicate discriminator value "
                            f"{wrap_val(tag)} used by both {variant_by_tag[tag].__name__} "
                            f"and {sub.__name__}"
                        )
                    variant_by_tag[tag] = sub
                    visit(sub)
                elif sub.__subclasses__():
                    visit(sub)
                else:
                    raise TypeError(
                        f"{self._description()}: {sub.__name__} is a subclass of "
                        f"{self._base_cls.__name__} but does not define "
                        f"{self._by_name} as a Constant"
                    )

        visit(self._base_cls)
        if not variant_by_tag:
            raise TypeError(
                f"{self._description()}: no variants found. A variant must be a "
                f"subclass of {self._base_cls.__name__} that sets "
                f"{self._by_name} = Constant(...)"
            )
        return variant_by_tag

    def _ensure_variants(self):
        if self._variants_by_tag is None:
            self._variants_by_tag = self._discover_variants()
        return self._variants_by_tag

    def __set__(self, instance, value):
        variants = self._ensure_variants()
        if not isinstance(value, tuple(variants.values())):
            valid = ", ".join(v.__name__ for v in variants.values())
            raise TypeError(
                f"{self._name}: Expected an instance of one of ({valid}); "
                f"Got {wrap_val(value)}"
            )
        super().__set__(instance, value)

    @property
    def get_type(self):
        variants = tuple(self._ensure_variants().values())
        return typing.Union[variants] if len(variants) > 1 else variants[0]

    def __str__(self):
        return f"<{self._description()}>"
