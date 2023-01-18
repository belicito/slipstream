import pytest
from enum import Enum
from slipstream.fsm import Machine, State


def test_2_states_flipping():
    m = Machine()
    on = State("On", on_entry=[lambda: print("state is ON")])
    off = State("Off", on_entry=[lambda: print("state is OFF")])
    m.add_states(on, off)
    flip = "Flip"

    on + flip >> off
    off + flip >> on

    m.start(initially=on)
    assert m.state() == on
    m.handle(flip)
    assert m.state() == off
    m.handle(flip)
    assert m.state() == on


def test_bulb_flipping_enum_entities():
    class Bulb(Enum):
        On = "On"
        Off = "Off"

    flip = "Flip"

    m = Machine()
    m.state(Bulb.On) + flip >> m.state(Bulb.Off)
    m.state(Bulb.Off) + flip >> m.state(Bulb.On)

    m.start(initially=Bulb.Off)
    assert m.state().id == Bulb.Off
    m.handle(flip)
    assert m.state().id == Bulb.On
    m.handle(flip)
    assert m.state().id == Bulb.Off
