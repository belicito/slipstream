import pytest
from slipstream.fsm import Machine

def test_2_states_flipping():
    m = Machine()
    on = m.get_state("On")
    on.add_entry(lambda: print("state is ON"))
    off = m.get_state("Off")
    off.add_entry(lambda: print("state is OFF"))
    flip = m.get_event("Flip")
    
    on + flip >> off
    off + flip >> on

    m.start(initially=on)
    assert m.state == on
    m.handle(flip)
    assert m.state == off
    m.handle(flip)
    assert m.state == on
