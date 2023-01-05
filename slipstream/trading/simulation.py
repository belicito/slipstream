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

    def __init__(self) -> None:
        self._prev_time = None
        self._cur_time = None
        self._pending_orders: List[Order] = []
        self._tracker = PositionTracker(price_multiplier=50.0)
        self.trades_path = f"/tmp/trades_{pydt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self._tracker.start_recording_trades(
            path=self.trades_path
        )
        print(f"Trades in {self.trades_path}")

        self.last_low = np.nan
        self.last_high = np.nan

        # Parameters for trading logics
        self.can_go_flat = False

        # Randomization factor: "act on prediction"
        self.act_on_pred = 1.

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

    def eval(self, bar: pd.Series, prediction: np.array) -> None:
        self.last_low, self.last_high = bar["Low"], bar["High"]
        self._tracker.eval_market_prices(bar["Low"], bar["High"])
        self.cur_time = bar["Timestamp"]
        self._eval_orders(low=bar["Low"], high=bar["High"])
        prediction = np.rint(prediction)
        
        if rrandom() > self.act_on_pred:
            return

        if self._is_up(prediction):
            self._go_long()
        elif self._is_down(prediction):
            self._go_short()
        elif self.can_go_flat:
            self._go_flat()

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
        for order in self._pending_orders:
            if order.type == OrderType.Market and self._pending_duration(order) >= self.MinOrderFillDelay:
                # Enhance: Should randomize fill price instead of always using worst
                if order.action in [OrderAction.Buy, OrderAction.BuyToCover]:
                    fill_price = (high + self.price_slip)
                else:
                    fill_price = (low - self.price_slip)
            elif order.type == OrderType.Limit and low <= order.limit <= high and self._pending_duration(order) >= self.MinOrderFillDelay:
                fill_price = order.limit
            else:
                self._fill_slip_bar_count += 1
                continue

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

    def _pending_duration(self, order: Order) -> pd.Timedelta:
        assert order.time_sent is not None, "Order has no sent time"
        return self.cur_time - order.time_sent

    def _is_up(self, prediction: np.array) -> bool:
        return int(prediction[0]) == 1

    def _is_down(self, prediction: np.array) -> bool:
        return int(prediction[2]) == 1

    def _place_limit(self, action: OrderAction, limit: float):
        self._pending_orders

    def _go_long(self):
        # TODO: should reconcile with any pending orders
        self._pending_orders = []
        if not self._tracker.is_long():
            order_size = 2 * self.ContractCount if self._tracker.is_short() else self.ContractCount
            order = Order(
                action=OrderAction.Buy,
                size=order_size,
                time_sent=self.cur_time
            )
            self._pending_orders.append(order)
            # print(f"Long at {order.time_sent}")

    def _go_short(self):
        # TODO: should reconcile with any pending orders
        self._pending_orders = []
        if not self._tracker.is_short():
            order_size = 2 * self.ContractCount if self._tracker.is_long() else self.ContractCount
            order = Order(
                action=OrderAction.Sell,
                size=order_size,
                time_sent=self.cur_time
            )
            self._pending_orders.append(order)
            # print(f"Short at {order.time_sent}")

    def _go_flat(self):
        self._pending_orders = []
        if not self._tracker.is_flat():
            action = OrderAction.Sell if self._tracker.is_long() else OrderAction.Buy
            order = Order(
                action=action,
                size=self._tracker.position.size,
                time_sent=self.cur_time
            )
            self._pending_orders.append(order)
            # print(f"Flat at {order.time_sent}")