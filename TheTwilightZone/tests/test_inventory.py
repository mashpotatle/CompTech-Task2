from systems.inventory import Inventory


def test_inventory_accepts_and_uses_items():
    inventory = Inventory()

    assert inventory.add_item("oxygen_tank") is True
    assert inventory.slots[0] == "oxygen_tank"

    inventory.active_index = 0
    used = inventory.use_active()
    assert used == "oxygen_tank"
    assert inventory.slots[0] is None


def test_inventory_drop_active_returns_item_and_clears_slot():
    inventory = Inventory()
    inventory.add_item("med_kit")
    inventory.active_index = 0

    dropped = inventory.drop_active()

    assert dropped == "med_kit"
    assert inventory.slots[0] is None


def test_inventory_cycles_slots_and_swaps_items():
    inventory = Inventory()
    inventory.add_item("med_kit")
    inventory.add_item("oxygen_tank")

    inventory.active_index = 0
    inventory.cycle(1)
    assert inventory.active_index == 1

    inventory.swap_slots(0, 1)
    assert inventory.slots[0] == "oxygen_tank"
    assert inventory.slots[1] == "med_kit"
