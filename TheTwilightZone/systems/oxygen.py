"""Oxygen management for the player character."""

from __future__ import annotations


class OxygenSystem:
    """Tracks player oxygen pressure while underwater.

    This is a small, data-driven system used by the game loop and HUD.
    The system can be extended later with current/vent effects or
    special recovery states, but the core contract is kept intentionally
    simple: oxygen drains while in water, can be restored with items,
    and triggers a "death" state once empty.
    """

    def __init__(
        self,
        max_oxygen: float = 100.0,
        drain_rate: float = 6.0,
        recovery_rate: float = 0.0,
    ) -> None:
        self.max_oxygen = float(max_oxygen)
        self.drain_rate = float(drain_rate)
        self.recovery_rate = float(recovery_rate)
        self.current = float(self.max_oxygen)

    @property
    def percent(self) -> float:
        return (self.current / self.max_oxygen) * 100.0 if self.max_oxygen else 0.0

    @property
    def is_empty(self) -> bool:
        return self.current <= 0.0

    def update(self, delta_time: float, in_water: bool = True) -> None:
        """Advance the oxygen timer for one frame."""
        dt = max(0.0, float(delta_time))

        if in_water and not self.is_empty:
            self.current = max(0.0, self.current - (self.drain_rate * dt))
            return

        if not in_water:
            self.current = min(self.max_oxygen, self.current + (self.recovery_rate * dt))

    def restore(self, amount: float) -> float:
        """Restore a bounded amount of oxygen and return the new value."""
        gain = max(0.0, float(amount))
        self.current = min(self.max_oxygen, self.current + gain)
        return self.current

    def set_to_full(self) -> None:
        self.current = self.max_oxygen

    def consume_for_use(self, amount: float) -> float:
        """Consume oxygen by some amount, used for item activation or emergencies."""
        cost = max(0.0, float(amount))
        self.current = max(0.0, self.current - cost)
        return self.current
