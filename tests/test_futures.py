from slipstream.market.futures import *


def test_ESH2():
    esh2 = EminiContract(2022, 3)
    assert esh2.expiry_time.month == 3
    print(esh2.expiry_time)
