from systems.oxygen import OxygenSystem


def test_oxygen_drains_when_in_water_and_recovers_when_used():
    system = OxygenSystem(max_oxygen=100.0, drain_rate=10.0)

    assert system.current == 100.0

    system.update(0.5, in_water=True)
    assert system.current < 100.0

    system.restore(25.0)
    assert system.current > 0.0


def test_oxygen_reaches_zero_and_marks_death_state():
    system = OxygenSystem(max_oxygen=100.0, drain_rate=100.0)

    system.update(1.0, in_water=True)

    assert system.current == 0.0
    assert system.is_empty is True
