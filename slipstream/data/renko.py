from typing import Iterable, List, Optional, Tuple
import math
import numpy as np
import pandas as pd
from typing import Union


__all__ = [
    "RenkoBuilder"
]


class RenkoBuilder:
    def __init__(self, bar_size: float) -> None:
        self._bar_size = bar_size
        self._last_price = np.nan
        self._lo_bound = np.nan
        self._hi_bound = np.nan

    def ingest(self, price: float) -> List[Tuple[float, float]]:
        """Ingest one price point and return list of Renko bars containing OHLC"""
        if np.isnan(self._last_price):
            self._last_price = math.floor(price)
            return []
        
        if np.isnan(self._lo_bound):
            # Assume initial trend with first two values
            if price > self._last_price:
                self._hi_bound = self._last_price + self._bar_size
                self._lo_bound = self._last_price - (2 * self._bar_size)
            else:
                self._lo_bound = self._last_price - self._bar_size
                self._hi_bound = self._last_price + (2 * self._bar_size)
            # return []

        ret_values = []
        while price >= self._hi_bound:
            open, close = self._hi_bound - self._bar_size, self._hi_bound
            ret_values.append((open, close))
            self._hi_bound += self._bar_size
            self._lo_bound += self._bar_size
        while price <= self._lo_bound:
            open, close = self._lo_bound + self._bar_size, self._lo_bound
            ret_values.append((open, close))
            self._hi_bound -= self._bar_size
            self._lo_bound -= self._bar_size
        return ret_values

    @staticmethod
    def get_dataframe(data: Union[pd.DataFrame, pd.Series, Iterable], bar_size: float, selector: str = "Close") -> pd.DataFrame:
        """Return Renko bars generated given data"""
        rb = RenkoBuilder(bar_size=bar_size)
        if isinstance(data, pd.Series):
            price_series = data
        elif isinstance(data, pd.DataFrame):
            price_series = data[selector]
        else:
            raise ValueError("Only Pandas DataFrame or Series")
        renko_bars = []
        indices = []
        for idx, val in price_series.items():
            rbars = rb.ingest(price=val)
            if len(rbars) == 0:
                continue
            renko_bars.extend(rbars)
            indices.extend([idx] * len(rbars))
        return pd.DataFrame(renko_bars, columns=["Open", "Close"], index=indices)


class Renko:
    """Iterator class to return Renko bars as list of tuple: (index, open, high, low, close)"""

    def __init__(self, s: pd.Series, bar_size: float):
        assert len(s) > 1, "Series of 2+ numbers needed"
        self.s = s
        self.size = bar_size

    def __iter__(self):
        # Assume initial trend with first two values
        if self.s[1] > self.s[0]:
            _hi_bound = self.s[0] + self.size
            _lo_bound = self.s[0] - (2 * self.size)
        else:
            _lo_bound = self.s[0] - self.size
            _hi_bound = self.s[0] + (2 * self.size)

        for i, x in self.s.iloc[1:].items():
            while x >= _hi_bound:
                yield (i, _hi_bound - self.size, _hi_bound, _hi_bound - self.size, _hi_bound)
                _hi_bound += self.size
                _lo_bound += self.size
            while x <= _lo_bound:
                yield (i, _lo_bound + self.size, _lo_bound + self.size, _lo_bound, _lo_bound)
                _hi_bound -= self.size
                _lo_bound -= self.size

    @staticmethod
    def get_dataframe(s: pd.Series, bar_size: float) -> pd.DataFrame:
        ar = np.array(list(Renko(s, bar_size)))
        assert ar.shape[1] == 5, "Expected rows of tuple: (index, open, high, low, close)"
        df = pd.DataFrame(
            {
                "Open": ar[:, 1],
                "High": ar[:, 2],
                "Low": ar[:, 3],
                "Close": ar[:, 4],
            },
            index=ar[:, 0]
        )
        return df
