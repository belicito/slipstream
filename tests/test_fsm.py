import pytest
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
    assert m.state == on
    m.handle(flip)
    assert m.state == off
    m.handle(flip)
    assert m.state == on
