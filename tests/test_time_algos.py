import pandas as pd
from slipstream.data.timeutils import TimestampAlgos


def test_weekday_anchoring():
    # saturday = pd.Timestamp("2023-07-29T13:37:35", tz="US/Central")
    # friday = TimestampAlgos.anchor_timestamp(saturday, 5)
    # assert friday.isoweekday() == 5

    monday = pd.Timestamp("2023-07-24T13:37:35", tz="US/Central")
    friday = TimestampAlgos.anchor_timestamp(monday, 5)
    assert friday.isoweekday() == 5
