"""
Morning vs EOD comparison logic.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional
from app.calculations.engine import SprintCalculationResult, DeveloperStats


@dataclass
class DeveloperMovement:
    name: str
    morning_assigned: float = 0.0
    morning_completed: float = 0.0
    morning_pct: float = 0.0
    eod_assigned: float = 0.0
    eod_completed: float = 0.0
    eod_pct: float = 0.0
    movement_pct: float = 0.0  # EOD % - Morning %


@dataclass
class SprintMovementResult:
    developer_movements: Dict[str, DeveloperMovement] = field(default_factory=dict)
    morning_total_scope: float = 0.0
    morning_completed: float = 0.0
    morning_pct: float = 0.0
    eod_total_scope: float = 0.0
    eod_completed: float = 0.0
    eod_pct: float = 0.0
    scope_change: float = 0.0
    daily_movement: float = 0.0  # EOD % - Morning %


def compute_movement(
    morning: Optional[SprintCalculationResult],
    eod: SprintCalculationResult,
    day1_fixed_scope: Optional[float] = None,
) -> SprintMovementResult:
    """Compare morning and EOD snapshots."""
    mv = SprintMovementResult()

    mv.eod_total_scope = eod.total_scope
    mv.eod_completed = eod.total_completed_sp
    mv.eod_pct = _overall_pct(eod, day1_fixed_scope)

    if morning:
        mv.morning_total_scope = morning.total_scope
        mv.morning_completed = morning.total_completed_sp
        mv.morning_pct = _overall_pct(morning, day1_fixed_scope)
        mv.scope_change = round(
            eod.total_scope - (day1_fixed_scope if day1_fixed_scope is not None else 0.0),
            2,
        )
        mv.daily_movement = round(
            _raw_overall_pct(eod, day1_fixed_scope)
            - _raw_overall_pct(morning, day1_fixed_scope),
            2,
        )

    # Developer movements
    all_devs = set(eod.developer_stats.keys())
    if morning:
        all_devs |= set(morning.developer_stats.keys())

    for dev in sorted(all_devs):
        eod_stats: DeveloperStats = eod.developer_stats.get(dev, DeveloperStats(name=dev))
        mov = DeveloperMovement(
            name=dev,
            eod_assigned=eod_stats.assigned_sp,
            eod_completed=eod_stats.completed_sp,
            eod_pct=eod_stats.completion_pct,
        )
        if morning:
            m_stats: DeveloperStats = morning.developer_stats.get(dev, DeveloperStats(name=dev))
            mov.morning_assigned = m_stats.assigned_sp
            mov.morning_completed = m_stats.completed_sp
            mov.morning_pct = m_stats.completion_pct
            mov.movement_pct = round(
                eod_stats.raw_completion_pct - m_stats.raw_completion_pct,
                2,
            )

        mv.developer_movements[dev] = mov

    return mv


def _raw_overall_pct(
    result: SprintCalculationResult,
    day1_fixed_scope: Optional[float],
) -> float:
    # Sprint completion is measured against the current full sprint scope.
    # Day-1 scope is a separate baseline used only for scope change.
    denominator = result.total_scope
    if denominator is None or denominator <= 0:
        return 0.0
    return result.total_completed_sp / denominator * 100


def _overall_pct(
    result: SprintCalculationResult,
    day1_fixed_scope: Optional[float],
) -> float:
    return round(_raw_overall_pct(result, day1_fixed_scope), 2)
