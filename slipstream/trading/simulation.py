from abc import abstractmethod

from slipstream.trading.model import PriceLike, OrderAction
from ..algos import *
import os
from .model import *
# from .pricing import *
from typing import List, Dict, Union, Any, Optional
from abc import ABC
import datetime as pydt
import numpy as np
from .positions import PositionTracker
from random import random as rrandom


class SimTrader:
    DefaultSize = 1
    TradeCost = 0.85
    SyntheticDelay = pd.Timedelta(milliseconds=1)
    MinOrderFillDelay = pd.Timedelta(milliseconds=500)

    def __init__(self, results_dir: str = "/tmp", *args, **kwargs) -> None:
        self._prev_time = None
        self._cur_time = None
        self._pending_orders: List[Order] = []
        self._last_known_prices: Optional[List[PriceLike]] = None
        self.tracker = PositionTracker(*args, **kwargs)

        self.results_dir = results_dir
        self.trades_path = os.path.join(
            self.results_dir,
            f"trades_{pydt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        self.tracker.start_recording_trades(
            path=self.trades_path
        )

        # Parameters for trading logics
        self.can_go_flat = False

        # Forceful application of price slippage
        self.price_slip = 0.

        # Collect execution delays for validatoin of trades
        self._exec_delays: List[pd.Timedelta] = []

        self._fill_slip_bar_count = 0

    def summarize(self) -> str:
        self.tracker.stop_recording_trades()
        output = (
            f"Number of trades : {len(self.tracker.trades)}\n"
            f"          Equity : {self.tracker.equity_value}\n"
            f"  Fill slip bars : {self._fill_slip_bar_count}"
        )
        return output

    def eval_market(self, time: pd.Timestamp, high: float, low: float) -> None:
        self._last_known_prices = [low, high]
        self.tracker.eval_market_prices(low, high)
        self.cur_time = time
        self._eval_orders(low=low, high=high)

    @property
    def cur_time(self) -> pd.Timestamp:
        assert self._cur_time is not None, "'cur_time' accessed before iterations start"
        return self._cur_time

    @cur_time.setter
    def cur_time(self, time: pd.Timestamp):
        self._prev_time = self._cur_time
        self._cur_time = time if self._cur_time is None else max(time, self._cur_time + self.SyntheticDelay)

    @property
    def execution_delays(self) -> pd.Series:
        return pd.Series(self._exec_delays)

    @property
    def trades(self) -> List[Trade]:
        return self.tracker.trades

    @property
    def cur_profit(self) -> PriceLike:
        return self.tracker.equity_value - self.tracker.initial_equity

    def _eval_orders(self, low: PriceLike, high: PriceLike):
        filled = []
        for order in self._pending_orders:
            if self._pending_duration(order) < self.MinOrderFillDelay:
                continue

            if order.is_stop_type() and not order.activated:
                self._eval_stop_activation(order, low=low, high=high)

            execution = None
            if self._is_active_market_order(order):
                execution = self._eval_market_order(order, low=low, high=high)
            elif self._is_active_limit_order(order):
                execution = self._eval_limit_order(order, low=low, high=high)
            else:
                self._fill_slip_bar_count += 1
                continue

            if execution:
                execution.time_received = order.time_sent
                execution.time_executed = self.cur_time
                self.tracker.add_execution(execution)
                filled.append(order)
                self._exec_delays.append(execution.time_executed - execution.time_received)
                self.on_order_filled(execution=execution)

        for order in filled:
            self._pending_orders.remove(order)

    def _is_active_market_order(self, order: Order) -> bool:
        return order.type == OrderType.Market or \
            (order.type in (OrderType.StopMarket, OrderType.TrailingStopMarket) and order.activated)

    def _is_active_limit_order(self, order: Order) -> bool:
        return order.type == OrderType.Limit or \
            (order.type in (OrderType.StopLimit, OrderType.TrailingStopLimit) and order.activated)

    def _is_unactivated_order(self, order: Order) -> bool:
        return (order.is_stop_type()) and not order.activated

    def _eval_stop_activation(self, order: Order, low: PriceLike, high: PriceLike):
        if order.activated:
            return
        
        # Find trigger for stop order
        if order.is_trailing_type():
            assert order.peak is not None, "Peak price is not available for trailing order"
            if order.is_buying():
                order.peak = min(order.peak, low)
                trigger = order.peak + order.stop
            else:
                order.peak = max(order.peak, high)
                trigger = order.peak - order.stop
        else:
            # If not trailing, stop is absolute price
            trigger = order.stop

        if order.is_buying() and trigger <= high:
            order.activated = True
        elif not order.is_buying() and trigger >= low:
            order.activated = True
 

    def _eval_market_order(self, order: Order, low: PriceLike, high: PriceLike) -> Optional[OrderExecution]:
        
        # TODO: Should randomize fill price instead of always using worst

        if order.action in [OrderAction.Buy, OrderAction.BuyToCover]:
            fill_price = (high + self.price_slip)
        else:
            fill_price = (low - self.price_slip)
        return OrderExecution(
            order,
            price=fill_price,
            cost=self.TradeCost * order.size
        )

    def _eval_limit_order(self, order: Order, low: PriceLike, high: PriceLike) -> Optional[OrderExecution]:
        fill_price = None
        if order.action in [OrderAction.Buy, OrderAction.BuyToCover]:
            if order.limit >= high:
                fill_price = high
        else:
            if order.limit <= low:
                fill_price = low
        
        if fill_price is not None:
            return OrderExecution(
                order,
                price=fill_price,
                size=order.size,
                cost=self.TradeCost * order.size
            )

        return None

    def _pending_duration(self, order: Order) -> pd.Timedelta:
        assert order.time_sent is not None, "Order has no sent time"
        return self.cur_time - order.time_sent

    def place_market(self, action: OrderAction, size: int = None) -> Order:
        size = size or self.DefaultSize
        order = Order(
            action=action,
            size=size,
            type=OrderType.Market,
            time_sent=self.cur_time
        )
        self._pending_orders.append(order)
        return order

    def place_stop_market(self, action: OrderAction, stop: PriceLike, size: int = None) -> Order:
        size = size or self.DefaultSize
        order = Order(
            action=action,
            size=size,
            type=OrderType.StopMarket,
            stop=stop,
            activated=False,
            time_sent=self.cur_time
        )
        self._pending_orders.append(order)
        return order

    def place_limit(self, action: OrderAction, limit: PriceLike, size: int = None) -> Order:
        size = size or self.DefaultSize
        order = Order(
            action=action,
            size=size,
            type=OrderType.Limit,
            limit=limit,
            time_sent=self.cur_time
        )
        self._pending_orders.append(order)
        return order

    def place_stop_limit(self, action: OrderAction, stop: PriceLike, limit: PriceLike, size: int = None) -> Order:
        size = size or self.DefaultSize
        order = Order(
            action=action,
            size=size,
            type=OrderType.StopLimit,
            limit=limit,
            stop=stop,
            activated=False,
            time_sent=self.cur_time
        )
        self._pending_orders.append(order)
        return order

    def place_trail_stop_market(self, action: OrderAction, stop: PriceLike, size: int = None) -> Order:
        size = size or self.DefaultSize
        if action in (OrderAction.Sell, OrderAction.SellShort):
            peak = self._last_known_prices[0]
        else:
            peak = self._last_known_prices[1]
        order = Order(
            action=action,
            size=size,
            type=OrderType.TrailingStopMarket,
            stop=stop,
            peak=peak,
            activated=False,
            time_sent=self.cur_time
        )
        self._pending_orders.append(order)
        return order

    def go_long(self):
        # TODO: should reconcile with any pending orders
        self._clear_pending_orders()
        if not self.tracker.is_long():
            order_size = 2 * self.DefaultSize if self.tracker.is_short() else self.DefaultSize
            order = Order(
                action=OrderAction.Buy,
                size=order_size,
                time_sent=self.cur_time
            )
            self._pending_orders.append(order)
            # print(f"Long at {order.time_sent}")

    def go_short(self):
        # TODO: should reconcile with any pending orders
        self._clear_pending_orders()
        if not self.tracker.is_short():
            order_size = 2 * self.DefaultSize if self.tracker.is_long() else self.DefaultSize
            order = Order(
                action=OrderAction.Sell,
                size=order_size,
                time_sent=self.cur_time
            )
            self._pending_orders.append(order)
            # print(f"Short at {order.time_sent}")

    def go_flat(self):
        self._clear_pending_orders()
        cur_pos = self.tracker.position
        if cur_pos is not None:
            action = OrderAction.Sell if self.tracker.is_long() else OrderAction.Buy
            order = Order(
                action=action,
                size=cur_pos.size,
                time_sent=self.cur_time
            )
            self._pending_orders.append(order)
            # print(f"Flat at {order.time_sent}")

    def _clear_pending_orders(self):
        self._pending_orders = []

    #----------------------------------------------------------------
    # Callbacks to be implemented by subclass
    #----------------------------------------------------------------

    def on_order_filled(self, execution: OrderExecution):
        """Subclasses override this method to react to orders getting filled."""
        pass
