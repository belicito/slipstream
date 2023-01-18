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
    ContractCount = 1
    TradeCost = 0.85
    SyntheticDelay = pd.Timedelta("1ms")
    MinOrderFillDelay = pd.Timedelta("10s")

    def __init__(self, results_dir: str = None) -> None:
        self._prev_time = None
        self._cur_time = None
        self._pending_orders: List[Order] = []
        self._tracker = PositionTracker(price_multiplier=50.0)

        self.results_dir = results_dir or "/tmp"
        self.trades_path = os.path.join(
            self.results_dir,
            f"trades_{pydt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        self._tracker.start_recording_trades(
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
        self._tracker.stop_recording_trades()
        output = (
            f"Number of trades : {len(self._tracker.trades)}\n"
            f"          Equity : {self._tracker.equity_value}\n"
            f"  Fill slip bars : {self._fill_slip_bar_count}"
        )
        return output

    def eval_market(self, time: pd.Timestamp, high: float, low: float) -> None:
        self._tracker.eval_market_prices(low, high)
        self.cur_time = time
        self._eval_orders(low=low, high=high)

    @property
    def cur_time(self) -> pd.Timestamp:
        assert self._cur_time is not None, "'cur_time' accessed before iterations start"
        return self._cur_time

    @cur_time.setter
    def cur_time(self, time: pd.Timestamp):
        self._prev_time = self._cur_time
        self._cur_time = max(time, self._cur_time + self.SyntheticDelay)

    @property
    def execution_delays(self) -> pd.Series:
        return pd.Series(self._exec_delays)

    def _eval_orders(self, low: PriceLike, high: PriceLike):
        filled = []
        # print(f"{len(self._pending_orders)} orders to eval...")
        for order in self._pending_orders:
            # print(f"Eval order: {order.action} {order.type} {order.size} {order.limit or ''}")
            if self._pending_duration(order) < self.MinOrderFillDelay:
                self._fill_slip_bar_count += 1
                continue

            fill_price = None
            if order.type == OrderType.Market:
                # Enhance: Should randomize fill price instead of always using worst
                if order.action in [OrderAction.Buy, OrderAction.BuyToCover]:
                    fill_price = (high + self.price_slip)
                else:
                    fill_price = (low - self.price_slip)

            elif order.type == OrderType.Limit:

                # TODO: Need more realistic fill logics for limit orders

                high_below_buy_limit = lambda: (
                    order.action in [OrderAction.Buy, OrderAction.BuyToCover] and
                    order.limit > high
                )
                low_above_sell_limit = lambda: (
                    order.action in [OrderAction.Sell, OrderAction.SellShort] and
                    order.limit < low
                )
                limit_between_hilo = lambda: low <= order.limit <= high

                if (high_below_buy_limit() or
                    low_above_sell_limit() or
                    limit_between_hilo()):
                    fill_price = order.limit

            if fill_price is not None:
                execution = OrderExecution(
                    order=order,
                    price=fill_price,
                    cost=self.TradeCost * order.size
                )
                execution.time_received = order.time_sent
                execution.time_executed = self.cur_time
                self._tracker.add_execution(execution)
                filled.append(order)
                self._exec_delays.append(execution.time_executed - execution.time_received)

        for order in filled:
            self._pending_orders.remove(order)

        # Leave this to the end so that other data structures are settled when callbacks are called
        for order in filled:
            self.on_order_filled(execution=execution)

    def _pending_duration(self, order: Order) -> pd.Timedelta:
        assert order.time_sent is not None, "Order has no sent time"
        return self.cur_time - order.time_sent

    def place_limit(self, action: OrderAction, limit: float, size: int = None) -> Order:
        size = size or self.ContractCount
        order = Order(
            action=action,
            size=size,
            type=OrderType.Limit,
            limit=limit,
            time_sent=self.cur_time
        )
        self._pending_orders.append(order)
        return order

    def go_long(self):
        # TODO: should reconcile with any pending orders
        if not self._tracker.is_long():
            order_size = 2 * self.ContractCount if self._tracker.is_short() else self.ContractCount
            order = Order(
                action=OrderAction.Buy,
                size=order_size,
                time_sent=self.cur_time
            )
            self._pending_orders.append(order)
            # print(f"Long at {order.time_sent}")

    def go_short(self):
        # TODO: should reconcile with any pending orders
        if not self._tracker.is_short():
            order_size = 2 * self.ContractCount if self._tracker.is_long() else self.ContractCount
            order = Order(
                action=OrderAction.Sell,
                size=order_size,
                time_sent=self.cur_time
            )
            self._pending_orders.append(order)
            # print(f"Short at {order.time_sent}")

    def go_flat(self):
        if not self._tracker.is_flat():
            action = OrderAction.Sell if self._tracker.is_long() else OrderAction.Buy
            order = Order(
                action=action,
                size=self._tracker.position.size,
                time_sent=self.cur_time
            )
            self._pending_orders.append(order)
            # print(f"Flat at {order.time_sent}")

    #----------------------------------------------------------------
    # Callbacks to be implemented by subclass
    #----------------------------------------------------------------

    def on_order_filled(self, execution: OrderExecution):
        pass
