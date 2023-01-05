from abc import ABC, abstractmethod
from .model import *
from typing import Optional


class Strategy(ABC):
    def observe_book_state(self, book_state: BookState):
        ...

