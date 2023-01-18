import numpy as np
import pandas as pd
from os import PathLike
from pathlib import Path
from typing import Any, Dict


class TradesAnalysis:
    def __init__(self, trades_csv: PathLike) -> None:
        self._df = pd.read_csv(trades_csv)
        self._df["Entry Time"] = pd.to_datetime(
            arg=self._df["Entry Time"], 
            infer_datetime_format=True
        )
        self._df["Exit Time"] = pd.to_datetime(
            arg=self._df["Exit Time"], 
            infer_datetime_format=True
        )

    @property
    def trades(self) -> pd.DataFrame:
        return self._df

    @property
    def winning_trades(self) -> pd.DataFrame:
        return self._df[self._df["Profit"] > 0.]

    @property
    def losing_trades(self) -> pd.DataFrame:
        return self._df[self._df["Profit"] < 0.]

    @property
    def neutral_trades(self) -> pd.DataFrame:
        return self._df[self._df["Profit"] == 0.]

    @property
    def market_durations(self) -> pd.Series:
        return self._df["Exit Time"] - self._df["Entry Time"]

    @property
    def sideline_durations(self) -> pd.Series:
        return self._df["Entry Time"] - self._df["Exit Time"].shift(periods=1)

    @staticmethod
    def _mean_std_min_max(s: pd.Series) -> str:
        return f"mean={s.mean()} stdev={s.std()} range=({s.min()}, {s.max()})"

    def in_market_time(self) -> float:
        total_time = self._df["Exit Time"].max() - self._df["Entry Time"].min()
        return self.market_durations.sum() / total_time

    def summary(self) -> Dict[str, Any]:
        trades = self.trades
        wins = self.winning_trades
        losses = self.losing_trades
        neutrals = self.neutral_trades
        
        return {
            "Trades": trades.shape[0],
            "Win Count": wins.shape[0],
            "Win Rate(%)": round(100. * wins.shape[0] / trades.shape[0], 2),
            "Loss Count": losses.shape[0],
            "Loss Rate(%)": round(100. * losses.shape[0] / trades.shape[0], 2),
            "Neutrals": neutrals.shape[0],
            "Profits (All)": self._mean_std_min_max(trades["Profit"]),
            "Run-Ups (All)": self._mean_std_min_max(trades["RunUp"]),
            "Draw-Downs (All)": self._mean_std_min_max(trades["DrawDown"]),
            "Profits (Win)": self._mean_std_min_max(wins["Profit"]),
            "Run-Ups (Win)": self._mean_std_min_max(wins["RunUp"]),
            "Draw-Downs (Win)": self._mean_std_min_max(wins["DrawDown"]),
            "Profits (Loss)": self._mean_std_min_max(losses["Profit"]),
            "Run-Ups (Loss)": self._mean_std_min_max(losses["RunUp"]),
            "Draw-Downs (Loss)": self._mean_std_min_max(losses["DrawDown"]),
            "Market Durations(mins)": self._mean_std_min_max(self.market_durations / pd.Timedelta("1m")),
            "Sideline Durations(mins)": self._mean_std_min_max(self.sideline_durations / pd.Timedelta("1m")),
            "In-Market Time": f"{100. * self.in_market_time():.2f}%"
        }
