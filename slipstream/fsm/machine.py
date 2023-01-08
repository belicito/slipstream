from typing import Any, Callable, Dict, List, Optional, Union


class _Trigger:
    def __init__(self, state: "State", event: "Event") -> None:
        self.state = state
        self.event = event

    def __rshift__(self, other):
        assert isinstance(other, State), f"Destination must be a state object"
        self.state.set_transition(event=self.event, dest=other)

        
class State:
    def __init__(self, name: str, machine: "Machine" = None, on_entry: List[Callable] = [], on_exit: List[Callable] = []) -> None:
        self.name = name
        self.machine = machine
        self.transition_map: Dict[Event, State] = {}
        self._entry_funcs = set(on_entry)
        self._exit_funcs = set(on_exit)

    def set_transition(self, event: "Event", dest: "State"):
        assert event.name not in self.transition_map, f"Transition already in place {self.name} + {event.name}"
        self.transition_map[event] = dest

    def __add__(self, other):
        if isinstance(other, str):
            event = self.machine.get_event(name=other)
        elif isinstance(other, Event):
            event = other
        else:
            raise ValueError(f"Unable to operate on object of {type(other)}")
        return _Trigger(state=self, event=event)

    def add_entry(self, f: callable):
        self._entry_funcs.add(f)

    def enter(self):
        for f in self._entry_funcs:
            f()

    def add_exit(self, f: callable):
        self._exit_funcs.add(f)

    def exit(self):
        for f in self._exit_funcs:
            f()


class Event:
    def __init__(self, name: str, machine: "Machine") -> None:
        self.name = name
        self.machine = machine

    def __add__(self, other):
        assert isinstance(other, State), f"Unable to operate on object of {type(other)}"
        return _Trigger(state=other, event=self)


EntityId = Union[str, State, Event]
Entity = Union[State, Event]


class Machine:

    DeadStateName = "<DEAD>"

    def __init__(self) -> None:
        self._started = False
        self._state = State(name=self.DeadStateName, machine=self)
        self._entity_map: Dict[str, Entity] = {}

    @property
    def started(self) -> bool:
        return self._started

    @property
    def state(self) -> State:
        return self._state

    def add_states(self, *states):
        for s in states:
            if isinstance(s, State):
                assert s.name not in self._entity_map, f"State name '{s.name}' already taken"
                s.machine = self
                self._entity_map[s.name] = s

    def make_state(self, name: str) -> State:
        assert name not in self._entity_map, f"Name '{name}' is already used in this state machine"
        state = State(name=name, machine=self)
        self._entity_map[name] = state
        return state

    def get_state(self, ident: EntityId, create: bool = True) -> Optional[State]:
        if isinstance(ident, State):
            assert ident.machine == self, "Given state does not belong to this state machine"
            return ident
        assert isinstance(ident, str), f"Cannot look for state with {type(ident)}"
        retval = self._entity_map.get(ident, None)
        if retval is not None:
            assert isinstance(retval, State), f"{ident} is not associated with a state but a {type(retval)}"
            return retval
        if create:
            return self.make_state(ident)
        return None

    def get_event(self, name: str, create: bool = True) -> Optional[Event]:
        retval = self._entity_map.get(name, None)
        if retval is not None:
            assert isinstance(retval, Event), f"{name} is not associated with a event but a {type(retval)}"
            return retval
        if create:
            return self.make_event(name)
        return None

    def make_event(self, name: str) -> Event:
        assert name not in self._entity_map, f"Name '{name}' is already used in this state machine"
        event = Event(name=name, machine=self)
        self._entity_map[name] = event
        return event

    def start(self, initially: EntityId):
        self._state = self.get_state(initially, create=False)
        assert self._state is not None, f"Initial state '{initially}' not found"
        self._started = True
        self._state.enter()

    def handle(self, event: Event):
        assert self.started, "Machine has not been started. Call start() first"
        next = self._state.transition_map.get(event, None)
        if next is not None:
            self._state.exit()
            self._state = next
            self._state.enter()
