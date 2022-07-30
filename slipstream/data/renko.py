from typing import Iterable
import pandas as pd


class Renko:
    class Iterator:
        def __init__(self, data: Iterable, brick: float):
            self.data = data
            self.brick = brick
            self.data_i = 0
            self.data_j = 0
            self.trend = 1

        def __next__(self):
            ret_val = self.data[self.data_i] + (self.trend * self.data_j * self.brick)
            # TODO: evaluate and advance data_i and data_j
            return ret_val

    def __init__(self, data: Iterable, brick_size: float):
        self.data = data
        self.brick_size = brick_size
        self._pandas_series: pd.Series = None

    @property
    def series(self) -> pd.Series:
        if self._pandas_series is None:
            self._create_series()
        return self._pandas_series

    def _create_series(self):
        raise NotImplementedError

    def __iter__(self):
        return self.Iterator(data=self.data, brick=self.brick_size)
