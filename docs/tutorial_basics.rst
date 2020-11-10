=================
Tutorial - Basics
=================

.. currentmodule:: typedpy

.. contents:: :local:


| Let's start with a scenario: You created a system that processes trades (we assume simple equity trades).
| A trade has many parameters. Some of them:
* price - a positive integer
* quantity
* Participants details
* identifiers of instrument
* date and time
* venue
| The trades are passed around by throughout the system. Often that will result in an unwieldy list of function parameters,
  or a dict with names of the fields and their value. This is an anti-pattern, since it relies on all the collaborators
  having knowledge about the implementation of the field names and values, as well as the hope that no one updated the
  dictionary. In short - a brittle code.
|
| Furthermore, typically every function/component validates the content of the parameters. This can result in a a lot
  of repetitive boilerplate code, or inconsistencies in the expectations from the values of the properties. For example, Different
  functions might expect different date format.
|
| Ideally, the specification should be expressed declaratively, and the trade object will be guaranteed to
  conform to the specs.
| This means that the validation is self-contained. Also, you may want a guarantee that the trade was not changed in
  any way.
| This where Typedpy shines. We could define something like the following:

.. code-block:: python

     class Trade(ImmutableStructure):
            price: DecimalNumber(maximum=10000, minimum=0)
            quantity: PositiveInt(maximum=100000, multiplesOf=5)
            symbol: String(pattern='[A-Z]', maxLength=6)
            denomination: Enum[Currency]
            participant_buyer: Trader
            participant_seller: Trader
            timestamp: DateField
            venue: Enum[Venue]

where:

.. code-block:: python

     class Trader(Structure):
            lei: String(pattern='[0-9A-Z]{18}[0-9]{2}$')
            alias: String(maxLength=32)

     class Venue(enum.Enum):
            NYSE = enum.auto()
            CBOT = enum.auto()
            AMEX = enum.auto()
            NASDAQ = enum.auto()

     class Currency(enum.Enum):
            USD = enum.auto()
            GBP = enum.auto()
            EUR = enum.auto()


| Now, we can pass trades around, and we are guaranteed that they are well formed and valid. There is no need to write
  boilerplate validation code in various functions again and again. Typedpy will block any attempt to create, or mutate
  a structure so that there is a point in time in which we have an invalid trade.
| Furthermore, since Trade is defined as immutable, we are guaranteed that no one tempered with them by accident. Again,
  Typedpy will block any such attempt.
| We also get a myriad of utilities, such as the ability to compare trades and print a trade, for free.


