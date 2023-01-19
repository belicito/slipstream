from typing import Iterable
import pandas as pd


class Renko:
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
