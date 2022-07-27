from typing import Union, Tuple
from .currency import Currency


class Price(float):
    def __init__(self, value, currency: Currency = None):
        self.currency = currency

    def __repr__(self):
        return self.currency.value_str(self) if self.currency else "$%.2f" % self


PriceLike = Union[float, Price]


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
