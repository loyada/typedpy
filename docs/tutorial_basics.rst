==========================
Tutorial - Getting Started
==========================


.. currentmodule:: typedpy

.. contents:: :local:


Basic Use-Case story
=====================


| Let's start with a scenario: You created a system that processes trades (we assume simple equity trades).
A trade has many parameters: price, quantity, Participants details, symbol, date and time, venue etc.

| The trades are passed around by throughout the system. Often that will result in an unwieldy list of function parameters,
or a dict with names of the fields and their value. This is an anti-pattern, since it relies on all the collaborators
somehow having precise knowledge about the implementation of the field names and values, as well as the hope that no invalid
trade or attribute was created by mistake, values extraction was bug-free (for example, someone reading "notional" as
float) and that no one updated the dictionary on purpose or by mistake.
| Another common problem is partially constructed instances. For example, when the developer forgot one of the fields.
| These are just some of the problems with having a loose definition of the API, or data. In short - we end up with a
brittle and unmaintainable code.
|
| Furthermore, typically every function/component validates the content of the parameters. This can result in a a lot
  of repetitive boilerplate code, or inconsistencies in the expectations from the values of the properties. For example, Different
  functions might expect different date format.
|
| Ideally, the specification should be expressed declaratively, and the trade object will be guaranteed to
  conform to the specs. In other words, we want the validation to be self-contained. Also, you may want a guarantee
  that the trade was not changed in any way during its processing.
| This is where Typedpy shines. We could define something like the following:

.. code-block:: python

     class Trade(ImmutableStructure):
            notional: DecimalNumber(maximum=10000, minimum=0)
            quantity: PositiveInt(maximum=100000, multiplesOf=5)
            symbol: String(pattern='[A-Z]+$', maxLength=6)
            denomination: Enum[Currency]
            participant_buyer: Trader
            participant_seller: Trader
            timestamp: DateField
            venue: Enum[Venue]
            id: String

where:

.. code-block:: python

     class Trader(ImmutableStructure):
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
  boilerplate validation code in various functions again and again. Typedpy **will block any attempt to create or mutate
  a structure so that at no point we might have an invalid instance**.
|
| Furthermore, since Trade is defined as immutable, we are guaranteed that no one tempered with them by accident. Again,
  Typedpy will block any such attempt.
| We also get a myriad of utilities, such as the ability to compare trades and print a trade, for free.


Structure Validation
====================
| After a while, we are told that the total value of our trades (notional * quantity) must not exceed 1,000,000 of the denomination.
| We also need to guarantee that the buyer is not the seller.
| This is trickier, since it involves interactions between two fields. Fortunately, this is supported:

.. code-block:: python

     MAX_ALLOWED_TOTAL_VALUE = 10000000

     class Trade(ImmutableStructure):
        .... # no change
        ....

         def __validate__(self):
             if self.quantity * self.notional > MAX_ALLOWED_TOTAL_VALUE:
                 raise ValueError("trade value is too high")
              if self.participant_seller == self.participant_buyer:
            raise ValueError("buyer cannot be seller")

And that's it.

Optionals
=========
Next, we are asked to add an *optional* comments field to trade.
This is done by updating the Trade structure as follows:

.. code-block:: python

     class Trade(ImmutableStructure):
        .... # no change
        ....
        comments: str
        _optional = ['comments']

or, alternatively:

.. code-block:: python

     from typing import Optional

     class Trade(ImmutableStructure):
        .... # no change
        ....
        comments: Optional[str]


Default value
=============
A business analyst asks you to change the default value for comments from None to "nothing to see here".
You do it by change the declaration as follows:

.. code-block:: python

     class Trade(ImmutableStructure):
        .... # no change
        ....
        comments: str = "Nothing to see here..."

Note that once we declared an explicit default value to a field, it is already implicitly already optional,
so there is no need to define it as such.

Serialization
=============
You create a web service that allows to query for a trade by its ID. You could write code to convert
the Trade instance to a serializable dictionary. But Typepy offers a simpler way:

.. code-block:: python

   output = Serializer(trade).serialize()

Next, you realize that that the client expects "buyer" instead of "participant_buyer", and "seller" instead
of "participant_seller". Let's do it:

.. code-block:: python

   mapper = {'participant_buyer': 'buyer',
             'participant_seller': 'seller'}
   output = Serializer(trade, mapper=mapper).serialize()

Deserialization
---------------
Next, you need to create an endpoint that allows to post trades. Instead of writing a lengthy validation
you can just create the following code:

.. code-block:: python

    class BadRequestException(Exception): pass

    try:
        Deserializer(Trade).deserializer(request.json)
    except Exception as e:
        BadRequestException(e)

Let's say that our web service uses Flask, then you may create an error handle:

.. code-block:: python

   def set_error_handlers(app: Flask):
       @app.errorhandler(BadRequestException)
       def invalid_request():
           return f'invalid request: {e}', HTTPStatus.BAD_REQUEST


This is nice, as it eliminates all the validation code, and the potential of impedance mismatch between
it and the definition of what constitutes a valid Trade.

Mapping to a JSON schema
========================
Another team builds a client of your service is Java. They are asking for a JSON or OpenAPI schema of your
API. You can provide create one with the following code:

.. code-block:: python

    schema, definitions = structure_to_schema(Trade, definitions_schema, {})


The **definitions** variable above is the schema of objects that are used in the main schema, and are referred to
from the main schema (e.g. : "$ref": "#/definitions/Trader").
The **schema** is the main schema for Trade.
