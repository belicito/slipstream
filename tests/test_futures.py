from slipstream.market.futures import *
import pandas as pd


def test_ESH2():
    esh2 = EminiContract(2022, 3)
    assert esh2.expiry_time.month == 3
    print(esh2.expiry_time)


def test_ESZ3():
    esz3 = EminiContract(2023, 12)
    sessions = []
    with open("/tmp/test_ESZ3.log", "wt+") as f:
        for s in esz3.trading_sessions(start=pd.Timestamp("2023-11-05", tz="us/central")):
            sessions.append(s)
            f.write(f"Session {len(sessions):>3}: from {s.begin} to {s.end}\n")
