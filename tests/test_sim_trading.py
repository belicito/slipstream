import pytest
from slipstream.trading.simulation import SimTrader
from slipstream.trading import TradeType, OrderAction, Order, OrderType, OrderExecution, Price, PriceLike
import pandas as pd


def test_market_order_fill():
    t0 = pd.Timestamp.now()
    dt = pd.Timedelta(seconds=1)
    sim = SimTrader()
    sim.eval_market(t0, low=10.0, high=10.2)
    order = sim.place_market(action=OrderAction.Buy, size=1)
    sim.eval_market(t0 + dt, low=10.0, high=10.2)
    p = sim.tracker.position
    assert p.trade_type == TradeType.Long
    assert p.size == 1

def test_limit_order_fill():
    t0 = pd.Timestamp.now()
    dt = pd.Timedelta(seconds=1)
    sim = SimTrader()
    sim.eval_market(t0, low=10.0, high=10.2)
    order = sim.place_limit(action=OrderAction.Buy, limit=9.7, size=1)
    sim.eval_market(t0 + dt, low=9.9, high=10.1)
    p = sim.tracker.position
    assert p == None

    sim.eval_market(t0 + 3 * dt, low=9.8, high=9.9)
    p = sim.tracker.position
    assert p == None
 
    sim.eval_market(t0 + 5 * dt, low=9.5, high=9.7)
    p = sim.tracker.position
    assert p.trade_type == TradeType.Long
    assert p.size == 1
 
def test_stop_order_fill():
    t0 = pd.Timestamp.now()
    dt = pd.Timedelta(seconds=1)
    sim = SimTrader()
    sim.eval_market(t0, low=10.0, high=10.2)
    order = sim.place_stop_market(action=OrderAction.Buy, stop=10.5, size=1)
    sim.eval_market(t0 + dt, low=10.0, high=10.2)
    p = sim.tracker.position
    assert p == None

    sim.eval_market(t0 + 2 * dt, low=10.3, high=10.4)
    p = sim.tracker.position
    assert p == None

    sim.eval_market(t0 + 3 * dt, low=10.4, high=10.5)
    p = sim.tracker.position
    assert p.trade_type == TradeType.Long
    assert p.size == 1

def test_stop_limit_order_fill():
    """
    |--------------------|--------------------|-------------------------|
                        9.8(trigger)          9.9(limit)             10.1(initial)
    """

    t0 = pd.Timestamp.now()
    dt = pd.Timedelta(seconds=1)
    sim = SimTrader()
    sim.eval_market(t0, low=10.0, high=10.2)
    order = sim.place_stop_limit(action=OrderAction.Sell, stop=9.8, limit=9.9, size=1)
    sim.eval_market(t0 + dt, low=10.0, high=10.1)
    p = sim.tracker.position
    assert p == None

    sim.eval_market(t0 + 2 * dt, low=9.9, high=10.0)
    p = sim.tracker.position
    assert p == None

    sim.eval_market(t0 + 3 * dt, low=9.8, high=9.9)  # Triggered here, but not fillable
    assert order.activated == True
    p = sim.tracker.position
    assert p == None

    sim.eval_market(t0 + 4 * dt, low=9.9, high=9.95)  # Filled
    p = sim.tracker.position
    assert p.trade_type == TradeType.Short
    assert p.size == 1

def test_trail_stop_market_fill():
    """
    stop = 1.5
    10.1 (initial)
    11.0
    12.0 (peak)
    11.0
    10.4 (exit)
    """
    
    t0 = pd.Timestamp.now()
    dt = pd.Timedelta(seconds=1)
    sim = SimTrader()
    sim.eval_market(t0, low=10.1, high=10.2)
    order = sim.place_trail_stop_market(action=OrderAction.Sell, stop=1.5, size=1)
    sim.eval_market(t0 + dt, low=10.2, high=10.3)
    sim.eval_market(t0 + 10 * dt, low=11.0, high=11.1)
    p = sim.tracker.position
    assert p == None
    sim.eval_market(t0 + 20 * dt, low=11.9, high=12.0)  # Peak
    p = sim.tracker.position
    assert p == None
    sim.eval_market(t0 + 30 * dt, low=11.0, high=11.1)
    p = sim.tracker.position
    assert p == None
    sim.eval_market(t0 + 40 * dt, low=10.3, high=10.4)  # Exit
    p = sim.tracker.position
    assert p.trade_type == TradeType.Short
    assert p.size == 1
