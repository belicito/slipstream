import os
import pandas as pd
import numpy as np
import pytz
from logging import info, warn, fatal, error, debug


class ESignal:
    @staticmethod
    def read_from_csv(path: str,
                      drop_useless_columns: bool = True,
                      do_save_cache: bool = True,
                      do_load_cache: bool = True) -> pd.DataFrame:
        path = os.path.abspath(path)
        cache_path = path + ".parquet"
        if do_load_cache and os.path.exists(cache_path):
            bars = pd.read_parquet(cache_path)
            return bars

        bars = pd.read_csv(path)
        if drop_useless_columns:
            bars = ESignal.drop_useless_cols()
        bars = ESignal.transform_date_time_columns(bars)
        if do_save_cache:
            bars.to_parquet(cache_path)

    @staticmethod
    def transform_date_time_columns(df: pd.DataFrame,
                                    date_col: str = "Date", time_col: str = "Time",
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
    def drop_useless_cols(df: pd.DataFrame) -> pd.DataFrame:
        to_be_yanked = [c for c in df.columns if c in ('Bar#', 'Bar Index', 'Tick Range')]
        if len(to_be_yanked) > 0:
            info(f"Will yank: {to_be_yanked}")
        retval = df.drop(columns=to_be_yanked)
        return retval
