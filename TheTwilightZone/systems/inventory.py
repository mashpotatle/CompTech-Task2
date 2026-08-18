"""Inventory and hotbar logic for the player."""

from __future__ import annotations

from dataclasses import dataclass, field


VALID_ITEMS = {"med_kit", "oxygen_tank"}
DISPLAY_LABELS = {
    "med_kit": "HP",
    "oxygen_tank": "O₂",
}


@dataclass
class Inventory:
    """Five-slot hotbar inventory used by the player.

    Slot values are string IDs such as "med_kit" and "oxygen_tank".
    """

    slots: list[str | None] = field(default_factory=lambda: [None] * 5)
    active_index: int = 0

    def _normalise_index(self, index: int) -> int:
        return max(0, min(len(self.slots) - 1, int(index)))

    def add_item(self, item_name: str) -> bool:
        if item_name not in VALID_ITEMS:
            return False

        for index, value in enumerate(self.slots):
            if value is None:
                self.slots[index] = item_name
                return True
        return False

    def remove_item(self, index: int) -> str | None:
        idx = self._normalise_index(index)
        item = self.slots[idx]
        self.slots[idx] = None
        return item

    def cycle(self, direction: int = 1) -> int:
        if not self.slots:
            return 0
        step = int(direction) or 1
        length = len(self.slots)
        self.active_index = (self.active_index + step) % length
        return self.active_index

    def swap_slots(self, first: int, second: int) -> None:
        a = self._normalise_index(first)
        b = self._normalise_index(second)
        self.slots[a], self.slots[b] = self.slots[b], self.slots[a]

    def use_active(self) -> str | None:
        item = self.slots[self.active_index]
        if item is None:
            return None
        self.slots[self.active_index] = None
        return item

    def drop_active(self) -> str | None:
        item = self.slots[self.active_index]
        if item is None:
            return None
        self.slots[self.active_index] = None
        return item

    @property
    def active_item(self) -> str | None:
        return self.slots[self.active_index] if 0 <= self.active_index < len(self.slots) else None

    def display_label(self, item_name: str | None) -> str:
        if item_name is None:
            return ""
        return DISPLAY_LABELS.get(item_name, item_name[:2].upper())
