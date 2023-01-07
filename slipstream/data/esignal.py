from typing import AnyStr, Union
import os
import pandas as pd
import numpy as np
import pytz
from logging import info, warn, fatal, error, debug


class ESignalCSV:
    def __init__(self, file: AnyStr, timezone: str = "EST"):
        self.path = os.path.abspath(file)
        self.timezone = timezone
        self.df: pd.DataFrame = None

    def get_dataframe(self, drop_useless_columns: bool = True,
                      do_load_cache: bool = True,
                      do_save_cache: bool = True) -> pd.DataFrame:
        if self.df is not None:
            return self.df

        path = os.path.abspath(self.path)
        cache_path = path + ".parquet"
        if do_load_cache and os.path.exists(cache_path):
            info(f"Cache found. loading {cache_path}")
            bars = pd.read_parquet(cache_path)
            return bars

        self.df = pd.read_csv(path)
        if drop_useless_columns:
            self.df = self._drop_useless_cols(self.df)

        timestamp_col = "Timestamp"
        self.df = self._transform_date_time_columns(self.df, out_col=timestamp_col, timezone=self.timezone)

        if do_save_cache:
            self.df.to_parquet(cache_path)
        return self.df

    @staticmethod
    def _transform_date_time_columns(df, date_col: str = "Date", time_col: str = "Time",
                                    out_col: str = "Timestamp", timezone: str = "EST",
                                    drop_cols: bool = True) -> pd.DataFrame:
        assert date_col in df and time_col in df, "Dataframe must have 'Date' or 'Time' columns"
        tees = pd.Series(np.empty(len(df))).apply(lambda t: 'T')
        datetime_strs = df[date_col] + tees + df[time_col]
        timestamps = pd.DatetimeIndex(datetime_strs, tz=pytz.timezone(timezone))

        if drop_cols:
            info(f"Dropping Date and Time columns")
            df = df.drop(columns=[date_col, time_col])
        df[out_col] = timestamps
        return df

    @staticmethod
    def _drop_useless_cols(df: pd.DataFrame) -> pd.DataFrame:
        useless_cols = ('Bar#', 'Bar Index', 'Tick Range')
        to_be_yanked = [c for c in df.columns if c in useless_cols]
        if len(to_be_yanked) > 0:
            debug(f"Will yank: {to_be_yanked}")
        retval = df.drop(columns=to_be_yanked)
        return retval
