.. Typedpy documentation master file, created by
   sphinx-quickstart on Sat Nov 18 02:27:20 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Typedpy's documentation!
===================================

``typedpy`` is a library for type-safe, strict, validated Python data structures, with serialization,
JSON Schema and IDE stub generation built in. A structure can never hold an invalid value: validation runs
when it is created **and on every change afterwards**, including changes inside nested lists and dicts.

It is pure Python with **zero dependencies**, supports Python 3.9-3.14, and has run in production,
including financial systems, since 2017.

Installation
------------

.. code-block:: bash

    pip install typedpy

or ``conda install -c conda-forge typedpy``.


Quick Start
-----------

.. code-block:: python

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

Fields can be typedpy field types with constraints (``String(maxLength=32)``), plain Python types
(``int``, ``str``), standard ``typing``/PEP 585 annotations (``list[str]``, ``Optional[...]``), other
structures, or any mix of them at any depth, e.g. ``Array[dict[String(minLength=5), int]]``.

A mutable :class:`Structure` is still validated on every change:

.. code-block:: python

    from typedpy import Structure

    class Order(Structure):
        quantity: PositiveInt
        tags: list[str]

    order = Order(quantity=5, tags=["a"])
    order.quantity = -1     # ValueError: quantity: Got -1; Expected a positive number
    order.tags.append(3)    # TypeError: ... Expected a string

The :doc:`tutorial_basics` walks through a fuller example step by step.


Features
--------

* **Deep immutability** - ``ImmutableStructure`` blocks reassignment *and* changes to nested lists, dicts
  and sets, and reads return defensive copies (:ref:`immutability`).

* **A field system that is plain object-oriented Python** - constraints are mixins that combine through
  inheritance (:ref:`extension-of-classes`), and any class can be used as a field
  (:ref:`arbitrary-classes`). Optional hooks plug a custom field into serialization, JSON Schema and stubs.

* **Discriminated unions** - :ref:`discriminated-union` picks the variant from a tag, using a real field
  reference rather than a string, and discovers variants automatically from subclasses.

* **Deriving models from existing ones** - ``Partial``, ``AllFieldsRequired``, ``Omit``, ``Pick`` and
  ``Extend``, like TypeScript's utility types (:ref:`structure-reuse`).

* **Enum-keyed structures** - ``@keys_of`` guarantees at import time that a structure has a field for every
  member of an enum (:ref:`keys-of`).

* **Undefined vs None** - an opt-in ``Undefined`` value distinct from ``None``, e.g. for PATCH-style APIs
  (:ref:`undefined-values`).

* **Serialization** - key mappers (camelCase, lowercase, renames, functions) that can be chained and compose
  through inheritance (:ref:`custom-mapping`), custom serialization (:ref:`custom-serialization`), and
  schema versioning (:doc:`versioning`).

* **Performance where it counts** - :ref:`trusted-deserialization` and :ref:`trusted-instantiation` skip
  validation for data you already trust, and :ref:`fast-serialization` is several times faster, still in
  pure Python.

* **JSON Schema in both directions** - generate a schema from structures, or structure code from a schema
  (:doc:`json_schema`).

* **IDE and type-checker support** - generated ``.pyi`` stubs turn typedpy fields back into ordinary type
  hints, so any IDE or type checker understands your structures (:doc:`stubs`).

* **Structured errors** - errors can be collected and returned as structured objects (:doc:`errors`).


Why Pure Python?
----------------

Typedpy is deliberately pure Python with no dependencies: you get full stack traces, it can be debugged and
audited end to end, there are no compiled builds, and the supply-chain surface is just this package. That
suits regulated and correctness-critical settings.

The trade-off is speed (see :doc:`limitations`). If validation dominates your workload, or you need
Pydantic's ecosystem, Pydantic is the better fit. Typedpy's strengths are elsewhere: deep immutability,
validation on every change, a simple extension model, and the features above. It also offers trusted
deserialization and fast serialization for the hot paths.


Contents:
=========
.. toctree::
   :maxdepth: 2

   tutorial_basics
   structures
   fields
   serialization
   versioning
   json_schema
   errors
   tutorial_dataclass_comparison
   limitations
   common_utilities
   stubs
   faq


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
