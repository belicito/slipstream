from typing import Union, Tuple, Callable, Iterable
from .currency import Currency


PriceLike = Union[int, float, 'Price']


class Price:
    def __init__(self, value: PriceLike, currency: Currency = None):
        if isinstance(value, Price):
            self.value = value.value
            self.currency = value.currency
        else:
            self.value = float(value)
            self.currency = currency

    def __repr__(self):
        return self.currency.value_str(self.value) if self.currency else "$%.2f" % self

    def __float__(self):
        return self.value

    def __int__(self):
        return int(self.value)

    def __eq__(self, other):
        return self._apply_to_comparable_prices((self, other), lambda x, y: x == y)

    def __ne__(self, other):
        return self._apply_to_comparable_prices((self, other), lambda x, y: x != y)

    def __gt__(self, other):
        return self._apply_to_comparable_prices((self, other), lambda x, y: x > y)

    def __ge__(self, other):
        return self._apply_to_comparable_prices((self, other), lambda x, y: x >= y)

    def __lt__(self, other):
        return self._apply_to_comparable_prices((self, other), lambda x, y: x < y)

    def __le__(self, other):
        return self._apply_to_comparable_prices((self, other), lambda x, y: x < y)

    def level(self) -> 'Price':
        """Returns equivalent value in default currency"""
        # TODO: return equivalent in USD
        return self

    @staticmethod
    def _apply_to_comparable_prices(price_likes: Iterable, callback: Callable):
        prices = [Price(x) for x in price_likes]
        price_0 = prices[0]
        for price in prices[1:]:
            if price.currency != price_0.currency:
                raise NotImplementedError("Comparison of prices in different currencies is not yet supported")
        price_values = [float(x) for x in prices]
        return callback(*price_values)

    def __add__(self, other):
        return Price(self.value + float(other), currency=self.currency)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return Price(self.value - float(other), currency=self.currency)

    def __rsub__(self, other):
        return Price(float(other) - self.value, currency=self.currency)

    def __mul__(self, other):
        return Price(self.value * float(other), currency=self.currency)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        return Price(self.value / float(other), currency=self.currency)

    def __rtruediv__(self, other):
        return Price(float(other) / self.value, currency=self.currency)


class PriceRange:
    def __init__(self, low: PriceLike = None, high: PriceLike = None,
                 prices: Tuple[PriceLike, PriceLike] = None,
                 inclusive: Tuple[bool, bool] = (True, True)):
        self.low = low
        self.high = high
        if prices:
            self.low, self.high = prices
        if inclusive:
            self.low_inclusive, self.high_inclusive = inclusive
        if not self.is_valid:
            raise ValueError(f"Invalid low and high prices: {self.low} and {self.high}")

    @property
    def is_valid(self) -> bool:
        return self.high is not None and self.low is not None and self.high >= self.low

    def includes(self, price: PriceLike):
        fits_low = self.low <= price if self.low_inclusive else self.low < price
        fits_high = price <= self.high if self.high_inclusive else price < self.high
        return fits_low and fits_high

    @property
    def hl2(self) -> PriceLike:
        return 0.5 * (self.low + self.high)

    def __repr__(self):
        low_bracket = "[" if self.low_inclusive else "("
        high_bracket = "]" if self.high_inclusive else ")"
        return f"{low_bracket}{self.low}, {self.high}{high_bracket}"
