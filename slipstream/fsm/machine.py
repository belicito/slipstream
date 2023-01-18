from typing import Any, Callable, Dict, Hashable, List, Optional, Union
from ..algos import *


class _Trigger:
    def __init__(self, state: "State", event: "Event") -> None:
        self.state = state
        self.event = event

    def __rshift__(self, other):
        assert isinstance(other, State), f"Destination must be a state object"
        self.state.set_transition(event=self.event, dest=other)

        
class State:
    def __init__(self, id: Hashable, machine: "Machine" = None, on_entry: List[Callable] = [], on_exit: List[Callable] = []) -> None:
        self.id = id
        self.machine = machine
        self.transition_map: Dict[Event, State] = {}
        self._entry_funcs = set(on_entry)
        self._exit_funcs = set(on_exit)

    def set_transition(self, event: "Event", dest: "State"):
        assert event.id not in self.transition_map, f"Transition already in place {self.id} + {event.id}"
        self.transition_map[event] = dest

    def __add__(self, other):
        if isinstance(other, Hashable):
            event = self.machine.event(id=other)
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

    def __hash__(self) -> int:
        return self.id.__hash__()


class Event:
    def __init__(self, id: Hashable, machine: "Machine", context: Any = None) -> None:
        self.id = id
        self.machine = machine
        self.context = context

    def __add__(self, other):
        assert isinstance(other, State), f"Unable to operate on object of {type(other)}"
        return _Trigger(state=other, event=self)

    def __hash__(self) -> int:
        return self.id.__hash__()
        

EntityIdentifying = Union[Hashable, State, Event]
Entity = Union[State, Event]


class Machine:

    DeadStateID = "<DEAD>"

    def __init__(self) -> None:
        self._started = False
        self._state = State(id=self.DeadStateID, machine=self)
        self._entity_map: Dict[Hashable, Entity] = {}

    @property
    def current_state(self) -> State:
        return self._state

    @property
    def started(self) -> bool:
        return self._started

    def add_states(self, *states):
        for s in states:
            if isinstance(s, State):
                assert s.id not in self._entity_map, f"State '{s.id}' already taken"
                s.machine = self
                self._entity_map[s.id] = s

    def state(self, id: EntityIdentifying = None, create: bool = True) -> Optional[State]:
        if id is None:
            return self.current_state
        if isinstance(id, State):
            assert id.machine == self, f"State {str(id)} does not belong to this state machine"
            return id

        # Look up the state
        assert isinstance(id, Hashable), f"Cannot look for state with {type(id)}"
        st = self._entity_map.get(id, None)
        if st is not None:
            assert isinstance(st, State), f"{str(id)} is not associated with a state but a {type(st)}"
            return st

        # Non-existent. Create
        if create:
            assert id not in self._entity_map, f"ID of '{str(id)}' is already used in this state machine"
            st = State(id=id, machine=self)
            self._entity_map[id] = st
            return st

        return None

    def event(self, id: Hashable, create: bool = True) -> Optional[Event]:
        ev = self._entity_map.get(id, None)
        if ev is not None:
            assert isinstance(ev, Event), f"{str(id)} is not associated with a event but a {type(ev)}"
            return ev

        if create:
            assert id not in self._entity_map, f"ID '{str(id)}' is already used in this state machine"
            ev = Event(id=id, machine=self)
            self._entity_map[id] = ev
            return ev

        return None

    def start(self, initially: EntityIdentifying):
        self._state = self.state(initially, create=False)
        assert self._state is not None, f"Initial state '{initially}' not found"
        self._started = True
        self._state.enter()

    def handle(self, event: EntityIdentifying):
        assert self.started, "Machine has not been started. Call start() first"
        if not isinstance(event, Event) and isinstance(event, Hashable):
            event_id = event
            event = self._entity_map.get(event_id, None)
        assert event is not None and isinstance(event, Event), f"No event '{str(event_id)}' in state machine"
        next = self._state.transition_map.get(event, None)
        if next is not None:
            # print(f" >>> {self._state.id} + {event.id} >> {next.id}")
            self._state.exit()
            self._state = next
            self._state.enter()

    def __call__(
        self, 
        state: EntityIdentifying = None,
        event: EntityIdentifying = None,
        create: bool = True
    ) -> Union[State, Event, None]:

        assert any_not_none(state, event), "Must pass in either state or event"
        if state is not None:
            return self.state(state, create=create)
        else:
            return self.event(event, create=create)
