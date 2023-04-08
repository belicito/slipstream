from typing import Iterable
import pandas as pd
import numpy as np


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
