import abc
from dataclasses import dataclass
import enum
import pandas as pd
from slipstream.data.timeutils import TimestampAlgos
from typing import Generator, Optional, SupportsFloat, Tuple
import pytz


__all__ = [
    "FutureContract",
    "EminiContract"
]


_1_DAY = pd.Timedelta(days=1)


class _ExpiryCode(enum.Enum):
    F = 1
    G = 2
    H = 3
    J = 4
    K = 5
    M = 6
    N = 7
    Q = 8
    U = 9
    V = 10
    X = 11
    Z = 12

    def month(self) -> int:
        return self.value   


@dataclass
class TradingSession:
    begin: pd.Timestamp
    end: pd.Timestamp


class FutureContract(abc.ABC):
    def __init__(self, multiplier: SupportsFloat, tick_size: SupportsFloat) -> None:
        self.multiplier = float(multiplier)
        self.tick_size = float(tick_size)

    @property
    @abc.abstractmethod
    def expiry_time(self) -> pd.Timestamp:
        """Expiry time for this contract"""
        pass

    @property
    @abc.abstractmethod
    def previous(self) -> "FutureContract":
        """Contract for the previous period"""
        pass

    @property
    @abc.abstractmethod
    def next(self) -> "FutureContract":
        """Contract for the next period"""
        pass

    def progress_in_cycle(self, ts: pd.Timestamp) -> float:
        """Progress in trading cycle(between expiries)"""
        last = self.previous.expiry_time
        this = self.expiry_time
        return (ts - last) / (this - last)
    
    def cycle_to_expiry(self, ts: pd.Timestamp) -> float:
        """Number of cycle until expiration. Eg., from previous expiry to this expiry is 1.0"""

        last = self.previous.expiry_time
        this = self.expiry_time
        assert ts <= this
        return (this - ts) / (this - last)

    @abc.abstractmethod
    def trading_sessions(self, start: Optional[pd.Timestamp] = None) -> Generator[TradingSession, None, None]:
        """Iterates through tuples of (start, end) times for trading sessions

        :param start: Start time for iterating. Default is 3 days before previous expiry
        """
        pass

    @abc.abstractmethod
    def trading_timezone(self) -> str:
        pass


class EminiContract(FutureContract):

    _allowed_months = [3, 6, 9, 12]

    def __init__(self, year: int, month: int, multiplier: float = 1.0, tick_size: float = 0.01) -> None:
        super().__init__(multiplier=multiplier, tick_size=tick_size)
        self.year = year
        self.month = month
        assert month in self._allowed_months, f"Invalid contract month {month}"
        self._expiry_time = TimestampAlgos.nth_isoweekday(year=year, month=month, nth=3, isoweekday=5)
        self._expiry_time = self.expiry_time.replace(hour=8, minute=30)
        self._expiry_time = self._expiry_time.tz_localize("US/Central")

    @property
    def expiry_time(self) -> pd.Timestamp:
        return self._expiry_time

    @property
    def next(self) -> FutureContract:
        year_delta, month_idx = divmod(self._allowed_months.index(self.month) + 1, 4)
        return EminiContract(
            year=self.year + year_delta, 
            month=self._allowed_months[month_idx],
            multiplier=self.multiplier,
            tick_size=self.tick_size,
        )

    @property
    def previous(self) -> FutureContract:
        year_delta, month_idx = divmod(self._allowed_months.index(self.month) - 1, 4)
        return EminiContract(
            year=self.year + year_delta, 
            month=self._allowed_months[month_idx],
            multiplier=self.multiplier,
            tick_size=self.tick_size,
        )

    def trading_sessions(self, start: Optional[pd.Timestamp] = None) -> Generator[TradingSession, None, None]:
        if start is None:
            start = self.expiry_time - self._default_cycle_timedelta
        ts = start.replace(hour=1, minute=0, second=0, microsecond=0)
        while ts < self.expiry_time:
            if 1 <= ts.isoweekday() <= 4 or ts.isoweekday() == 7:
                t0 = ts.replace(hour=17, minute=0)
                t1 = (t0 + _1_DAY).replace(hour=16, minute=0)
                s = TradingSession(begin=t0, end=min(t1, self._expiry_time))
                yield s
            ts = (ts + _1_DAY).replace(hour=1)

    def get_session_progress(self, ts: pd.Timestamp) -> float:
        """Given a timestamp, return a value between [0, 1] that indicates progress in the trading session"""
        sess_start = ts.replace(hour=17, minute=0, second=0, microsecond=0)
        if ts < sess_start:
            sess_start = sess_start - _1_DAY

        sess_end = ts.replace(hour=16, minute=0, second=0, microsecond=0)
        if ts > sess_end:
            sess_end = sess_end + _1_DAY

        retval = (ts - sess_start) / (sess_end - sess_start)
        # print("session progress:", ts, "->", retval, "Day:", sess_start, "-", sess_end)
        return retval

    def get_week_progress(self, ts: pd.Timestamp) -> float:
        """Given a timestamp, return a value between [0, 1] that indicates progress in the trading week"""

        ts_isoweekday = ts.isoweekday()
        days_from_sun = 0 if ts_isoweekday == 7 else ts_isoweekday
        week_start = ts.replace(hour=17, minute=0, second=0, microsecond=0) - days_from_sun * _1_DAY
        days_to_fri = 5 if ts_isoweekday == 7 else 5 - ts_isoweekday
        week_end = ts.replace(hour=16, minute=0, second=0, microsecond=0) + days_to_fri * _1_DAY
        retval = (ts - week_start) / (week_end - week_start)
        # print("week progress:", ts, "->", retval, "Week:", week_start, "-", week_end)
        return retval


    @property
    def _default_cycle_timedelta(self) -> pd.Timedelta:
        return pd.Timedelta(95, "D")

    def trading_timezone(self) -> str:
        return "US/Central"


def _infer_contract_year(year_str: str) -> int:
    cur_year_str = str(pd.Timestamp.now().year)
    result_year_str = cur_year_str[:-len(year_str)] + year_str
    return int(result_year_str)
