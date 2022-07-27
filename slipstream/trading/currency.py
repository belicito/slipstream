from abc import ABC, abstractmethod


class Currency(ABC):
    """Base class that represents a currency

    `List of world currencies: <https://www.countries-ofthe-world.com/world-currencies.html>`_
    """
    @property
    @abstractmethod
    def symbol(self) -> str:
        raise NotImplementedError

    def value_str(self, value: float) -> str:
        return "%s%.2f" % (self.symbol, value)


class USDollar(Currency):
    def symbol(self) -> str: return "USD"


class Euro(Currency):
    def symbol(self) -> str: return "EUR"


class PoundSterling(Currency):
    def symbol(self) -> str: return "GBP"


class JapaneseYen(Currency):
    def symbol(self) -> str: return "JPY"


class SouthKoreanWon(Currency):
    def symbol(self) -> str: return "KRW"


class HongKongDollar(Currency):
    def symbol(self) -> str: return "HKD"
