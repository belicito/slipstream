
import io
import numpy as np
from slipstream.algos import *
from slipstream.trading.model import *
from enum import IntEnum
from typing import Tuple, List, Any, Union
import logging

logging.basicConfig(level=logging.INFO)


class MeasuredTrade(Trade):
    """Monitored trades carry run_up and draw_down numbers on top of Trade
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_up = np.nan
        self.draw_down = np.nan

    def eval_market_high_low(self, high: Optional[PriceLike], low: Optional[PriceLike]):
        if high is None or low is None:
            return
        if self.type == TradeType.Long:
            self.run_up = self.size * self.price_mult * max(0, high - self.entry)
            self.draw_down = self.size * self.price_mult * min(0, low - self.entry)
        else:
            self.run_up = self.size * self.price_mult * max(0, self.entry - low)
            self.draw_down = self.size * self.price_mult * min(0, self.entry - high)

    def fields_to_log(self) -> List[str]:
        return super().fields_to_log() + [f"{self.run_up}", f"{self.draw_down}"]

    @classmethod
    def field_names_to_log(cls) -> List[str]:
        return super().field_names_to_log() + ["RunUp", "DrawDown"]


class Position:
    def __init__(self, trade_type: TradeType, size: int, entry: PriceLike, entry_cost: PriceLike):
        self.trade_type = trade_type
        self._size = size
        self.entry = entry
        self.trading_cost = Price(entry_cost)
        self.time_entered: Optional[pd.Timestamp] = None
        self.market_low: Optional[PriceLike] = None
        self.market_high: Optional[PriceLike] = None

    @property
    def size(self) -> int:
        return self._size

    @size.setter
    def size(self, new_size: int):
        assert new_size <= self._size, "You may only reduce size of created position"
        self.trading_cost *= (new_size / self._size)
        self._size = new_size

    @property
    def cost(self) -> Price:
        return self.trading_cost

    @staticmethod
    def from_execution(execution: OrderExecution) -> 'Position':
        pos = Position(trade_type=TradeType.from_order_action(execution.order.action),
                       size=execution.size,
                       entry=execution.price,
                       entry_cost=execution.cost)
        pos.time_entered = pd.Timestamp(execution.time_executed)
        return pos

    def partial_cost(self, size: Optional[int] = None, ratio: Optional[float] = None) -> Price:
        if size is not None:
            return self.cost * (size / self.size)
        elif ratio is not None:
            assert ratio <= 1.0, "'ratio' should be <= 1.0"
            return self.cost * ratio
        else:
            raise ValueError("Must provide 'size' or 'ratio'")

    def eval_market_prices(self, *prices):
        for price in prices:
            self.market_low = price if self.market_low is None else min(self.market_low, price)
            self.market_high = price if self.market_high is None else max(self.market_high, price)

    def is_same_side(self, execution: OrderExecution) -> bool:
        return (
            self.trade_type == TradeType.Long and 
            execution.order.action in (OrderAction.Buy, OrderAction.BuyToCover)
        ) or (
            self.trade_type == TradeType.Short and 
            execution.order.action in (OrderAction.Sell, OrderAction.SellShort)
        )

    def duplicate(self) -> 'Position':
        pos = Position(
            trade_type=self.trade_type,
            size=self.size,
            entry=self.entry,
            entry_cost=self.trading_cost
        )
        return pos

    def merge(self, other: 'Position'):
        assert other.trade_type == self.trade_type
        my_total_price = self.size * self.entry
        its_total_price = other.size * other.entry
        self._size += other.size
        self.entry = (my_total_price + its_total_price) / self._size
        self.trading_cost += other.trading_cost

    def __repr__(self):
        return f"<{self.trade_type.name} {self.size} at {self.entry}>"


class PositionTracker:
    def __init__(self, initial_equity: float = 10000.0, buy_cost: float = 0, sell_cost: float = 0, price_multiplier: float = 1.0):
        self.trades: List[Trade] = []
        self.open_positions: List[Position] = []
        self.initial_equity = initial_equity
        self.equity_value = initial_equity
        self._aggregated_position = None
        self._trades_sink: Optional[io.TextIOWrapper] = None
        self._price_mult = price_multiplier

    def start_recording_trades(self, path: str):
        if self._trades_sink is None:
            logging.info(f"Logging trades to {path}")
            self._trades_sink = open(path, "wt+")
            self._trades_sink.reconfigure(write_through=True)
            self._trades_sink.write(",".join(MeasuredTrade.field_names_to_log()))
            self._trades_sink.write("\n")
            self._trades_sink.flush()

    def stop_recording_trades(self):
        if self._trades_sink is not None:
            self._trades_sink.close()

    def is_long(self) -> bool:
        return self.position is not None and self.position.trade_type == TradeType.Long
        
    def is_short(self) -> bool:
        return self.position is not None and self.position.trade_type == TradeType.Short
        
    def is_flat(self) -> bool:
        return self.position is None

    @property
    def position(self) -> Optional[Position]:
        if self._aggregated_position is None and len(self.open_positions) > 0:
            pos = self.open_positions[0]
            self._aggregated_position = pos.duplicate()
            for pos in self.open_positions[1:]:
                self._aggregated_position.merge(pos)
        return self._aggregated_position

    def add_execution(self, execution: OrderExecution):
        if len(self.open_positions) == 0 or self.position is not None and self.position.is_same_side(execution):
            self.open_positions.append(Position.from_execution(execution))
        else:
            residual_exec = self._reduce_position(execution)
            if residual_exec is not None:
                assert len(self.open_positions) == 0
                self.open_positions.append(Position.from_execution(residual_exec))
        self._aggregated_position = None
        self.equity_value -= execution.cost

    def _reduce_position(self, execution: OrderExecution) -> Optional[OrderExecution]:
        """Deduct from open positions given order execution. If currently open position is smaller than given execution,
        return the residual execution size."""
        if len(self.open_positions) == 0:
            return execution
        position = self.open_positions.pop(0)
        
        deduct_size = min(position.size, execution.size)
        assert deduct_size > 0
        trade = MeasuredTrade(
            trade_type=position.trade_type,
            size=deduct_size,
            entry=position.entry,
            exit=execution.price,
            cost=position.partial_cost(size=deduct_size) + execution.partial_cost(size=deduct_size),
            price_mult=self._price_mult
        )
        trade.time_entered = position.time_entered if position.time_entered else pd.Timestamp.now(tz="utc")
        trade.time_exited = execution.time_executed
        trade.eval_market_high_low(high=position.market_high, low=position.market_low)
        self._add_trade(trade)
        self.equity_value += trade.profit

        position.size = max(0, position.size - deduct_size)
        if position.size > 0:
            self.open_positions.insert(0, position)

        execution.size = max(0, execution.size - deduct_size)
        if execution.size == 0:
            return None
        else:
            return self._reduce_position(execution)


    def _add_trade(self, trade: Trade):
        if self._trades_sink is not None:
            self._trades_sink.write(",".join(trade.fields_to_log()))
            self._trades_sink.write("\n")
            self._trades_sink.flush()
        self.trades.append(trade)

    def _to_loggable(self, field: Any) -> str:
        if type(field) is str and field.startswith("$"):
            return str(field[1:])
        return str(field)

    def eval_market_prices(self, *prices):
        for position in self.open_positions:
            position.eval_market_prices(*prices)
