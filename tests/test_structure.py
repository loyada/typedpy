import enum

from typedpy import Structure, DecimalNumber, PositiveInt, String, Enum


class Venue(enum.Enum):
    NYSE = enum.auto()
    CBOT = enum.auto()
    AMEX = enum.auto()
    NASDAQ = enum.auto()


class Trader(Structure):
    lei: String(pattern='[0-9A-Z]{18}[0-9]{2}$')
    alias: String(maxLength=32)


def test_optional_fields():
    class Trade(Structure):
        notional: DecimalNumber(maximum=10000, minimum=0)
        quantity: PositiveInt(maximum=100000, multiplesOf=5)
        symbol: String(pattern='[A-Z]+$', maxLength=6)
        buyer: Trader
        seller: Trader
        venue: Enum[Venue]
        comment: String
        _optional = ["comment", "venue"]

    assert set(Trade._required) == {'notional', 'quantity', 'symbol', 'buyer', 'seller'}
    Trade(notional=1000, quantity=150, symbol="APPL",
          buyer=Trader(lei="12345678901234567890", alias="GSET"),
          seller=Trader(lei="12345678901234567888", alias="MSIM"),
          timestamp="01/30/20 05:35:35",
          )
