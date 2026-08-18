from entities.silt_cloud import SiltCloud
from entities.thermal_vent import ThermalVent


def test_silt_cloud_has_visibility_and_speed_reduction():
    cloud = SiltCloud(position=(0.0, 0.0), radius=80.0, visibility=0.15)

    assert cloud.visibility_reduction > 0.0
    assert cloud.visibility_reduction < 1.0
    assert cloud.speed_reduction < 1.0
    assert cloud.speed_reduction > 0.0


def test_thermal_vent_damage_falls_off_with_distance():
    vent = ThermalVent(
        position=(0.0, 0.0),
        heat_radius=100.0,
        heat_damage=8.0,
        eruption_damage=30.0,
    )

    close_damage = vent.get_damage_at_distance(0.0)
    mid_damage = vent.get_damage_at_distance(50.0)
    far_damage = vent.get_damage_at_distance(150.0)

    assert close_damage > mid_damage > far_damage >= 0.0


def test_thermal_vent_direction_and_effect_properties_are_applied():
    vent = ThermalVent(
        position=(10.0, 15.0),
        direction=(0.0, 0.0),
        radius=30.0,
        haze_length=120.0,
        haze_width=40.0,
        bubble_count=9,
        bubble_spread=12.0,
        bubble_speed=1.5,
    )

    # Zero-length direction should fall back to +X and remain normalised.
    assert vent.direction.x == 1.0
    assert vent.direction.y == 0.0

    assert vent.radius == 30.0
    assert vent.haze_length == 120.0
    assert vent.haze_width == 40.0
    assert vent.bubble_count == 9
    assert vent.bubble_spread == 12.0
    assert vent.bubble_speed == 1.5
