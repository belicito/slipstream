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
