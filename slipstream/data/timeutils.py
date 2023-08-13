import numpy as np
import pandas as pd


class TimestampAlgos:
    SECS_IN_DAY = 3600 * 24
    SECS_IN_WEEK = 3600 * 24 * 7

    @staticmethod
    def elapsed_day(dt_series: pd.Series) -> pd.Series:
        def elapsed_day(ts: pd.Timestamp):
            return ((ts.hour * 3600.0) + (ts.minute * 60.0) + ts.second) / TimestampAlgos.SECS_IN_DAY
        retval = dt_series.apply(elapsed_day)
        return retval

    @staticmethod
    def elapsed_week(ts_series: pd.Series) -> pd.Series:
        def elapsed_week(ts: pd.Timestamp):
            return (ts.day_of_week + 1) / 7
        retval = ts_series.apply(elapsed_week)
        return retval

    @staticmethod
    def nth_isoweekday(year: int, month: int, nth: int, isoweekday: int) -> pd.Timestamp:
        """Return Timestamp for the specific ISO weekday of given year-month"""

        assert 1 <= month <= 12, "Month must be in range {1,...,12}"
        assert 1 <= isoweekday <= 7, "ISO weekday must be in range {1,...,7}"
        ts = pd.Timestamp(year=year, month=month, day=1)
        remaining = nth
        for day in range(ts.day, ts.days_in_month + 1):
            ts = ts.replace(day=day)
            if ts.isoweekday() == isoweekday:
                remaining -= 1
            if remaining == 0:
                return ts
        raise ValueError(f"Cannot find ISO weekday {isoweekday} in {nth}th week of {ts.month_name()}")

    @staticmethod
    def anchor_timestamp(ts: pd.Timestamp, isoweekday: int) -> pd.Timestamp:
        """Anchor given timestamp to the specified ISO weekday in the same week"""

        weekday_delta = ts.isoweekday() - isoweekday
        return ts - weekday_delta * pd.Timedelta(1, "D")

    @staticmethod
    def reset_timestamps(
        s: pd.Series,
        isoweekday: int = -1,
        hour: int = -1,
        minute: int = -1,
        second: int = -1,
        microsecond: int = -1
    ) -> pd.Series:
        """
        Reset a series of timestamps to specified isoweekday, hour, minute, second, etc.
        Default is no change
        """

        # TODO: implement
        return s
