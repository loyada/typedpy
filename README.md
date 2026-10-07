[![][GA img]][GA]
[![][docs img]][docs]
[![][pypi img]][pypi]
[![][conda-forge img]][conda-forge]
[![][license img]][license]

# Typedpy - Strict Type System for Python

`typedpy` is a library for type-safe, strict, validated Python data structures, with
serialization, JSON Schema and IDE stub generation built in. A structure can never hold an
invalid value: validation runs when it is created **and on every change afterwards**,
including changes inside nested lists and dicts.

It is pure Python with **zero dependencies**, supports Python 3.9-3.14, and has run in
production, including financial systems, since 2017.

```
pip install typedpy
```

(or `conda install -c conda-forge typedpy`)

## Quick start

```python
import enum
from typing import Optional

from typedpy import (
    ImmutableStructure, String, PositiveInt, Float, Enum,
    Serializer, Deserializer, mappers,
)


class Currency(enum.Enum):
    USD = 1
    EUR = 2


class Trader(ImmutableStructure):
    lei: String(pattern="[0-9A-Z]{18}[0-9]{2}$")
    alias: String(maxLength=32)

    _serialization_mapper = mappers.TO_CAMELCASE


class Trade(ImmutableStructure):
    order_id: String
    symbol: String(pattern="[A-Z]+$", maxLength=6)
    quantity: PositiveInt(multiplesOf=5)
    price: Float(minimum=0)
    currency: Enum[Currency]
    buyer: Trader
    tags: list[str]
    comment: Optional[str]

    _serialization_mapper = mappers.TO_CAMELCASE


# deserialize (and validate) JSON-like input; keys are camelCase on the wire
trade = Deserializer(Trade).deserialize({
    "orderId": "T-1001",
    "symbol": "AAPL",
    "quantity": 100,
    "price": 231.5,
    "currency": "USD",
    "buyer": {"lei": "5493001KJTIIGC8Y1R12", "alias": "desk-7"},
    "tags": ["equity"],
})
assert trade.currency is Currency.USD

Trade(order_id="T-1", symbol="AAPL", quantity=-5, price=1.0,
      currency=Currency.USD, buyer=trade.buyer, tags=[])
# ValueError: Trade.quantity: Got -5; Expected a positive number

trade.quantity = 200        # ValueError: Trade: Structure is immutable
trade.tags.append("bond")   # ValueError: tags: Field is immutable  (deep immutability)

Serializer(trade).serialize()
# {'orderId': 'T-1001', 'symbol': 'AAPL', 'quantity': 100, ..., 'buyer': {'lei': ..., 'alias': 'desk-7'}}
```

Fields can be typedpy field types with constraints (`String(maxLength=32)`), plain Python
types (`int`, `str`), standard `typing`/PEP 585 annotations (`list[str]`, `Optional[...]`),
other structures, or any mix of them at any depth, e.g. `Array[dict[String(minLength=5), int]]`.

A mutable `Structure` is still validated on every change:

```python
from typedpy import Structure

class Order(Structure):
    quantity: PositiveInt
    tags: list[str]

order = Order(quantity=5, tags=["a"])
order.quantity = -1     # ValueError: quantity: Got -1; Expected a positive number
order.tags.append(3)    # TypeError: ... Expected a string
```

## Highlights

### Deep immutability

`ImmutableStructure` blocks reassignment **and** changes to nested lists, dicts and sets,
reads return defensive copies, and later changes to the caller's input don't leak in.
(`@dataclass(frozen=True)` and Pydantic's `frozen` only block reassignment.) Individual fields
can be made immutable too (`ImmutableField`, `ImmutableArray`, `ImmutableMap`...).

### A field system that is plain object-oriented Python

A custom field is an ordinary class. Constraints are mixins that combine through inheritance:

```python
from typedpy import Field, Integer, Positive

class Even(Field):
    def __set__(self, instance, value):
        if value % 2:
            raise ValueError(f"{self._name}: Got {value}; Expected an even number")
        super().__set__(instance, value)

class EvenPositiveInt(Integer, Positive, Even):
    pass

class Batch(Structure):
    size: EvenPositiveInt

Batch(size=3)   # ValueError: Batch.size: Got 3; Expected an even number
```

Optional hooks plug a custom field into everything else: `SerializableField` for
serialization, `to_json_schema`/`from_json_schema` for JSON Schema, and `get_type` for stubs.
Classes you don't own can be used directly as field types, or wrapped with
`create_typed_field`.

### Discriminated unions

The discriminator is a real field reference (refactor-safe), and variants are discovered
automatically from subclasses, so there's no `Union[...]` to forget to update:

```python
from typedpy import AbstractStructure, Constant, DiscriminatedUnion

class Shape(AbstractStructure):
    kind: String

class Circle(Shape):
    kind = Constant("circle")
    radius: float

class Square(Shape):
    kind = Constant("square")
    side: float

class Drawing(Structure):
    shapes: list[DiscriminatedUnion(Shape, by=Shape.kind)]

drawing = Deserializer(Drawing).deserialize(
    {"shapes": [{"kind": "circle", "radius": 1.0}, {"kind": "square", "side": 2.0}]}
)
assert [type(s) for s in drawing.shapes] == [Circle, Square]
```

Unrelated classes work too: `DiscriminatedUnion(Union[Circle, Square], by=Circle.kind)`.

### Deriving models from existing ones

`Partial`, `AllFieldsRequired`, `Omit`, `Pick` and `Extend` work like TypeScript's utility
types. They copy fields rather than inherit, so they work on immutable classes too:

```python
from typedpy import Partial, Omit

class TradeUpdate(Partial[Omit[Trade, ("buyer", "currency")]]):
    pass

TradeUpdate(quantity=50)   # every remaining field is optional
```

### Enum-keyed structures: `@keys_of`

Guarantee at import time that a structure has a field for every member of an enum, like
TypeScript's `Record<Role, ...>`. Adding an enum member without updating the class fails fast:

```python
from typedpy import keys_of

class Role(enum.Enum):
    admin = 1
    engineer = 2
    sales = 3

@keys_of(Role)
class SalaryBands(Structure):
    admin: int
    engineer: int
# TypeError: SalaryBands: missing fields: sales
```

### `Undefined` vs `None`

Opt in to a real "no value" that is distinct from `None`, e.g. for PATCH-style APIs:

```python
from typedpy import Undefined

class Patch(Structure):
    name: str
    email: str
    _required = []
    _ignore_none = True
    _enable_undefined_value = True

patch = Deserializer(Patch).deserialize({"email": None})
assert patch.name is Undefined and patch.email is None
Serializer(patch).serialize()   # {'email': None}
```

### Serialization

* Key mappers (`TO_CAMELCASE`, `TO_LOWERCASE`, rename dicts, function mappers), which can be
  **chained** as a list and **compose through inheritance**.
* Schema versioning: a `Versioned` structure is migrated to its latest schema on
  deserialization.
* **Trusted deserialization** for data you already trust (e.g. your own database), which
  skips validation and is several times faster, with a unit-test helper to make sure a class
  stays eligible:

  ```python
  trade = Deserializer(Trade).deserialize(row, direct_trusted_mapping=True)

  # in a unit test:
  from typedpy.testing import assert_trusted_deserialization_mapper_is_safe
  assert_trusted_deserialization_mapper_is_safe(Trade)
  ```

* **Fast serialization**: mark a class `FastSerializable` and call `create_serializer(cls)`
  for roughly 4-5x faster serialization, still in pure Python.
* Pickling support.

### JSON Schema, in both directions

```python
from typedpy import structure_to_schema, schema_to_struct_code

schema, definitions = structure_to_schema(Trader, {})
print(schema_to_struct_code("Trader", schema, definitions))
# class Trader(Structure):
#     lei: String(pattern='[0-9A-Z]{18}[0-9]{2}$')
#     alias: String(maxLength=32)
#
#     _required = ['alias', 'lei']
```

### IDE and type-checker support through generated stubs

typedpy generates `.pyi` stubs that turn its field types back into ordinary type hints, with
full `__init__` signatures, so any IDE or type checker understands your structures (no plugin
needed):

```
create-stubs-for-dir <src_root_dir> <directory>
create-stub <src_root_dir> <path/to/module.py>
```

### Also included

Structured, collectable errors (`ErrorInfo`), cross-field validation via `__validate__`,
`AbstractStructure`/`FinalStructure`, `shallow_clone_with_overrides`, `deep_get`, `typedpy.testing.find_diff`,
`@default_factories`, and global defaults through `TypedPyDefaults`.

## Why pure Python?

typedpy is deliberately pure Python with no dependencies: you get full stack traces, it can
be debugged and audited end to end, there are no compiled builds, and the supply-chain
surface is just this package. That suits regulated and correctness-critical settings.

The trade-off is speed: validation is slower than Pydantic's Rust core. If validation
dominates your workload, or you need Pydantic's ecosystem (FastAPI, SQLModel, settings),
Pydantic is the better fit. typedpy's strengths are elsewhere: deep immutability, validation
on every change, a simple extension model, and the features above. It also offers trusted
deserialization and fast serialization for the hot paths.

## Documentation

Full documentation: **[typedpy.readthedocs.io](https://typedpy.readthedocs.io)**, including
a [tutorial](https://typedpy.readthedocs.io/en/latest/tutorial_basics.html),
[structures](https://typedpy.readthedocs.io/en/latest/structures.html),
[fields](https://typedpy.readthedocs.io/en/latest/fields.html),
[serialization](https://typedpy.readthedocs.io/en/latest/serialization.html),
[JSON Schema](https://typedpy.readthedocs.io/en/latest/json_schema.html),
[stubs](https://typedpy.readthedocs.io/en/latest/stubs.html) and
[limitations](https://typedpy.readthedocs.io/en/latest/limitations.html).

The [tests](https://github.com/loyada/typedpy/tree/master/tests) are also a large
collection of working examples.

## License

MIT. See [LICENSE.txt](https://github.com/loyada/typedpy/blob/master/LICENSE.txt).

[GA]:https://github.com/loyada/typedpy/actions
[GA img]:https://github.com/loyada/typedpy/actions/workflows/main.yml/badge.svg

[docs img]:https://readthedocs.org/projects/typedpy/badge/?version=latest
[docs]:https://typedpy.readthedocs.io/en/latest/?badge=latest

[license]:https://github.com/loyada/typedpy/blob/master/LICENSE.txt
[license img]:https://img.shields.io/badge/License-MIT-blue.svg

[conda-forge]:https://anaconda.org/conda-forge/typedpy/
[conda-forge img]:https://anaconda.org/conda-forge/typedpy/badges/installer/conda.svg

[pypi]:https://pypi.org/project/typedpy/
[pypi img]:https://img.shields.io/pypi/v/typedpy.svg
