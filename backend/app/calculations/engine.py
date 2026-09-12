"""
Core deterministic calculation engine.
All SP and completion % figures are calculated here.
AI never touches these numbers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class StoryAllocation:
    issue_key: str
    summary: str
    status: str
    developer: Optional[str]
    sp: Optional[float]
    is_completed: bool
    source: str  # "dev1", "dev2", "assignee", "none"
    raw_row_index: int


@dataclass
class DeveloperStats:
    name: str
    assigned_sp: float = 0.0
    completed_sp: float = 0.0

    @property
    def remaining_sp(self) -> float:
        return max(0.0, self.assigned_sp - self.completed_sp)

    @property
    def completion_pct(self) -> float:
        return round(self.raw_completion_pct, 2)

    @property
    def raw_completion_pct(self) -> float:
        if self.assigned_sp == 0:
            return 0.0
        return self.completed_sp / self.assigned_sp * 100


@dataclass
class SprintMetadata:
    name: str
    sprint_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@dataclass
class SprintCalculationResult:
    # Developer-level
    developer_stats: Dict[str, DeveloperStats] = field(default_factory=dict)

    # Sprint-level
    total_scope: float = 0.0           # sum of ALL story SP in the CSV (scope)
    total_completed_sp: float = 0.0    # sum of SP for completed stories (scope-based)
    total_remaining_sp: float = 0.0
    overall_completion_pct: float = 0.0

    # Story counts
    total_stories: int = 0
    completed_stories: int = 0
    open_stories: int = 0
    stories_without_sp: int = 0
    stories_without_dev: int = 0

    # Warnings and audit records
    warnings: List[str] = field(default_factory=list)
    data_quality_issues: List[dict] = field(default_factory=list)
    allocations: List[StoryAllocation] = field(default_factory=list)

    # Sprint metadata
    sprint_name: Optional[str] = None
    sprint_id: Optional[str] = None
    sprint_start: Optional[str] = None
    sprint_end: Optional[str] = None
    detected_columns: List[str] = field(default_factory=list)

    def ordered_developer_stats(self, order: List[str]) -> List[DeveloperStats]:
        """Return developer stats in the given fixed order, then any extras."""
        result = []
        for name in order:
            if name in self.developer_stats:
                result.append(self.developer_stats[name])
        # Append any developers found in data but NOT in the fixed order list
        for name, stats in self.developer_stats.items():
            if name not in order:
                result.append(stats)
        return result


# ---------------------------------------------------------------------------
# Calculation engine
# ---------------------------------------------------------------------------

class SprintCalculationEngine:
    """
    Pure calculation logic — no I/O, no AI, no side effects.
    Accepts a list of parsed row dicts and returns SprintCalculationResult.
    """

    def __init__(self, team_members: List[str], completed_statuses: List[str]):
        self.team_members = [m.strip() for m in team_members]
        self.completed_statuses = [s.strip().lower() for s in completed_statuses]

    def calculate(self, rows: List[dict], detected_columns: List[str]) -> SprintCalculationResult:
        result = SprintCalculationResult(detected_columns=detected_columns)
        allocations: List[StoryAllocation] = []
        seen_allocations: Dict[str, set] = {}  # issue_key -> set of developers already allocated

        def audit_issue(issue_key: str, status: Optional[str], assignee: Optional[str], problem: str, *,
                        dev1: Optional[str] = None, dev2: Optional[str] = None, dev3: Optional[str] = None,
                        sp1: Optional[str] = None, sp2: Optional[str] = None, sp3: Optional[str] = None) -> None:
            entry = {
                "issue_key": issue_key,
                "status": status or "",
                "assignee": assignee or "",
                "developer_owner_1": dev1 or "",
                "developer_owner_2": dev2 or "",
                "developer_owner_3": dev3 or "",
                "sp_owner_1": sp1 or "",
                "sp_owner_2": sp2 or "",
                "sp_owner_3": sp3 or "",
                "problem_description": problem,
            }
            result.data_quality_issues.append(entry)

        for idx, row in enumerate(rows):
            issue_key = self._get(row, ["Issue key", "issue key", "Issue Key"]) or f"ROW_{idx}"
            summary = self._get(row, ["Summary", "summary"]) or ""
            status = self._get(row, ["Status", "status"]) or ""
            assignee = self._clean_name(self._get(row, ["Assignee", "assignee"]))

            if not status:
                result.warnings.append(f"⚠ {issue_key}: Missing status — skipped from completion calculation.")
                audit_issue(
                    issue_key, status, assignee,
                    "Missing status; story skipped from completion calculation.",
                )

            result.total_stories += 1
            is_completed = status.strip().lower() in self.completed_statuses

            if is_completed:
                result.completed_stories += 1
            else:
                result.open_stories += 1

            # Jira exports are not consistent about the custom-field prefix or
            # how many developer allocation columns they contain.  Discover
            # numbered developer/SP pairs from the actual headers.
            allocation_fields = self._allocation_fields(row)
            first_owner = allocation_fields.pop(0) if allocation_fields else (None, None, None)
            first_owner_number, dev1_name, dev1_sp_raw = first_owner
            dev1_sp = self._parse_sp(dev1_sp_raw)
            if dev1_sp_raw is not None and dev1_sp is None and dev1_sp_raw not in ("", "nan", "None"):
                try:
                    raw_val = float(dev1_sp_raw)
                    if raw_val < 0:
                        result.warnings.append(f"⚠ {issue_key}: Dev Owner 1 SP is negative ({raw_val}) — skipped.")
                        audit_issue(
                            issue_key, status, assignee,
                            f"Developer Owner 1 SP is negative ({raw_val}) and was skipped.",
                            dev1=dev1_name if 'dev1_name' in locals() else None,
                            dev2=dev2_name if 'dev2_name' in locals() else None,
                            sp1=dev1_sp_raw if 'dev1_sp_raw' in locals() else None,
                            sp2=dev2_sp_raw if 'dev2_sp_raw' in locals() else None,
                        )
                except (ValueError, TypeError):
                    pass

            # Remaining discovered allocations are handled below (rather than
            # assuming Jira only exports Developer 1 and Developer 2).
            second_owner = allocation_fields.pop(0) if allocation_fields else (None, None, None)
            second_owner_number, dev2_name, dev2_sp_raw = second_owner
            dev2_sp = self._parse_sp(dev2_sp_raw)
            if dev2_sp_raw is not None and dev2_sp is None and dev2_sp_raw not in ("", "nan", "None"):
                try:
                    raw_val = float(dev2_sp_raw)
                    if raw_val < 0:
                        result.warnings.append(f"⚠ {issue_key}: Dev Owner 2 SP is negative ({raw_val}) — skipped.")
                        audit_issue(
                            issue_key, status, assignee,
                            f"Developer Owner 2 SP is negative ({raw_val}) and was skipped.",
                            dev1=dev1_name if 'dev1_name' in locals() else None,
                            dev2=dev2_name if 'dev2_name' in locals() else None,
                            sp1=dev1_sp_raw if 'dev1_sp_raw' in locals() else None,
                            sp2=dev2_sp_raw if 'dev2_sp_raw' in locals() else None,
                        )
                except (ValueError, TypeError):
                    pass

            # Fallback: Assignee + Story point estimate (spec §5 — exact field priority)
            assignee = self._clean_name(self._get(row, ["Assignee", "assignee"]))
            story_pts_raw = self._story_point_value(row)
            story_pts = self._parse_sp(story_pts_raw)
            if story_pts_raw is None:
                result.stories_without_sp += 1
                result.warnings.append(
                    f"⚠ {issue_key}: Missing Story Point Estimate."
                )
                audit_issue(
                    issue_key, status, assignee,
                    "Missing Story Point Estimate.",
                    dev1=dev1_name, dev2=dev2_name,
                    sp1=dev1_sp_raw, sp2=dev2_sp_raw,
                )
            elif story_pts is None:
                result.stories_without_sp += 1
                result.warnings.append(
                    f"⚠ {issue_key}: Invalid Story Point Estimate ({story_pts_raw})."
                )
                audit_issue(
                    issue_key, status, assignee,
                    f"Invalid Story Point Estimate ({story_pts_raw}).",
                    dev1=dev1_name, dev2=dev2_name,
                    sp1=dev1_sp_raw, sp2=dev2_sp_raw,
                )

            allocated = False
            owner_allocation_seen = False

            # Priority 1: Dev1 + SP1
            if dev1_name and dev1_sp is not None:
                owner_allocation_seen = True
                if self._is_team_member(dev1_name):
                    allocations.append(StoryAllocation(
                        issue_key=issue_key,
                        summary=summary,
                        status=status,
                        developer=dev1_name,
                        sp=dev1_sp,
                        is_completed=is_completed,
                        source=f"OWNER_{first_owner_number or 1}",
                        raw_row_index=idx,
                    ))
                    self._accumulate(result, dev1_name, dev1_sp, is_completed)
                    seen_allocations.setdefault(issue_key, set()).add(dev1_name)
                    allocated = True
                else:
                    result.warnings.append(
                        f"⚠ {issue_key}: Developer 1 '{dev1_name}' not in team — allocation skipped."
                    )

            # Priority 2+: developer/SP pairs (duplicate developers on one
            # story are counted once, while distinct developers are retained).
            for pair_index, (owner_number, candidate_name, candidate_sp_raw) in enumerate(
                [(second_owner_number, dev2_name, dev2_sp_raw), *allocation_fields]
            ):
                candidate_sp = self._parse_sp(candidate_sp_raw)
                if not candidate_name or candidate_sp is None:
                    continue
                owner_allocation_seen = True
                dev2_name, dev2_sp = candidate_name, candidate_sp
                if self._is_team_member(dev2_name):
                    if dev2_name not in seen_allocations.get(issue_key, set()):
                        allocations.append(StoryAllocation(
                            issue_key=issue_key,
                            summary=summary,
                            status=status,
                            developer=dev2_name,
                            sp=dev2_sp,
                            is_completed=is_completed,
                            source=f"OWNER_{owner_number or pair_index + 2}",
                            raw_row_index=idx,
                        ))
                        self._accumulate(result, dev2_name, dev2_sp, is_completed)
                        seen_allocations.setdefault(issue_key, set()).add(dev2_name)
                        allocated = True
                    else:
                        result.warnings.append(
                            f"⚠ {issue_key}: Duplicate allocation for '{dev2_name}' skipped."
                        )
                else:
                    result.warnings.append(
                        f"⚠ {issue_key}: Developer 2 '{dev2_name}' not in team — allocation skipped."
                    )

            # Fallback: Assignee + story_pts (only if no dev1/dev2 allocation was made)
            if not allocated and not owner_allocation_seen:
                if assignee and story_pts is not None:
                    if self._is_team_member(assignee):
                        allocations.append(StoryAllocation(
                            issue_key=issue_key,
                            summary=summary,
                            status=status,
                            developer=assignee,
                            sp=story_pts,
                            is_completed=is_completed,
                            source="assignee",
                            raw_row_index=idx,
                        ))
                        self._accumulate(result, assignee, story_pts, is_completed)
                        allocated = True
                    else:
                        # Assignee not in team — mark as without dev
                        pass

            if not allocated:
                allocations.append(StoryAllocation(
                    issue_key=issue_key,
                    summary=summary,
                    status=status,
                    developer=None,
                    sp=story_pts,
                    is_completed=is_completed,
                    source="none",
                    raw_row_index=idx,
                ))
                result.stories_without_dev += 1
                if dev1_name and dev1_sp_raw is None:
                    result.warnings.append(
                        f"⚠ {issue_key}: Developer Owner 1 is present but its Dev SP is missing."
                    )
                    audit_issue(
                        issue_key, status, assignee,
                        "Developer Owner 1 is present but its Dev SP is missing.",
                        dev1=dev1_name, dev2=dev2_name,
                        sp1=dev1_sp_raw, sp2=dev2_sp_raw,
                    )
                if assignee is None:
                    result.warnings.append(
                        f"⚠ {issue_key}: Missing Assignee when developer fallback is required."
                    )
                    audit_issue(
                        issue_key, status, assignee,
                        "Missing Assignee when developer fallback is required.",
                        dev1=dev1_name, dev2=dev2_name,
                        sp1=dev1_sp_raw, sp2=dev2_sp_raw,
                    )

        # ── Sprint-level scope totals (story-scope based, per spec §14 & §20) ──
        # total_scope  = sum of Story Point Estimate for ALL stories in the sprint
        # total_completed_sp = sum of Story Point Estimate for COMPLETED stories
        # These are independent of developer allocation.
        raw_scope_total = 0.0
        raw_completed_total = 0.0
        for row in rows:
            sp_val = self._parse_sp(self._story_point_value(row))
            if sp_val is None:
                # Some Jira configurations expose only per-developer SP
                # columns. In that case the story scope is their sum.
                sp_val = round(sum(
                    parsed for _, _, raw in self._allocation_fields(row)
                    if (parsed := self._parse_sp(raw)) is not None
                ), 2) or None
            if sp_val is None:
                continue
            status = self._get(row, ["Status", "status"]) or ""
            raw_scope_total += sp_val
            if status.strip().lower() in self.completed_statuses:
                raw_completed_total += sp_val

        result.total_scope = round(raw_scope_total, 2)
        result.total_completed_sp = round(raw_completed_total, 2)
        result.total_remaining_sp = round(raw_scope_total - raw_completed_total, 2)

        if result.total_scope > 0:
            result.overall_completion_pct = round(
                result.total_completed_sp / result.total_scope * 100, 2
            )
        else:
            result.overall_completion_pct = 0.0

        result.allocations = allocations

        # Detect sprint metadata from Jira's Sprint field. Jira exports may
        # provide a plain sprint name or a GreenHopper metadata string.
        sprint_values = [
            row.get("Sprint", row.get("sprint", ""))
            for row in rows
            if row.get("Sprint") or row.get("sprint")
        ]
        if sprint_values:
            metadata = self._parse_sprint_metadata(
                max(set(sprint_values), key=sprint_values.count)
            )
            result.sprint_name = metadata.name
            result.sprint_id = metadata.sprint_id
            result.sprint_start = metadata.start_date
            result.sprint_end = metadata.end_date

        logger.info(
            "Calculation complete: %d stories, scope=%.2f, completed=%.2f, pct=%.2f%%",
            result.total_stories,
            result.total_scope,
            result.total_completed_sp,
            result.overall_completion_pct,
        )
        return result

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _accumulate(
        self,
        result: SprintCalculationResult,
        dev_name: str,
        sp: float,
        is_completed: bool,
    ) -> None:
        if dev_name not in result.developer_stats:
            result.developer_stats[dev_name] = DeveloperStats(name=dev_name)
        stats = result.developer_stats[dev_name]
        stats.assigned_sp = round(stats.assigned_sp + sp, 2)
        if is_completed:
            stats.completed_sp = round(stats.completed_sp + sp, 2)

    def _is_team_member(self, name: Optional[str]) -> bool:
        if not name:
            return False
        return name.strip() in self.team_members

    @staticmethod
    def _get(row: dict, keys: List[str]) -> Optional[str]:
        for key in keys:
            val = row.get(key)
            if val is not None and str(val).strip() not in ("", "nan", "None"):
                return str(val).strip()
        wanted = {re.sub(r"[^a-z0-9]+", " ", key.lower()).strip() for key in keys}
        for actual_key, val in row.items():
            normalized = re.sub(r"[^a-z0-9]+", " ", str(actual_key).lower()).strip()
            if normalized in wanted and val is not None and str(val).strip().lower() not in ("", "nan", "none"):
                return str(val).strip()
        return None

    @staticmethod
    def _story_point_value(row: dict) -> Optional[str]:
        """Find the populated Jira story-point estimate column dynamically."""
        preferred = [
            "Custom field (Story point estimate)",
            "Story point estimate",
            "Custom field (Story Points)",
            "Story Points",
        ]
        value = SprintCalculationEngine._get(row, preferred)
        if value is not None:
            return value
        for key, raw_value in row.items():
            normalized = re.sub(r"[^a-z0-9]+", " ", str(key).lower()).strip()
            if "story point" in normalized or "story points" in normalized:
                if raw_value is not None and str(raw_value).strip().lower() not in (
                    "", "nan", "none"
                ):
                    return str(raw_value).strip()
        return None

    @classmethod
    def _allocation_fields(
        cls, row: dict
    ) -> List[tuple[Optional[str], Optional[str], Optional[str]]]:
        """Return all developer/SP pairs in numeric column order."""
        names: Dict[str, str] = {}
        points: Dict[str, str] = {}
        for key in row:
            normalized = re.sub(r"[^a-z0-9]+", " ", str(key).lower()).strip()
            number_match = re.search(
                r"(?:developer(?: owner)?|dev owner)\s*(\d+)",
                normalized,
            )
            if not number_match:
                continue
            number = number_match.group(1)
            if "developer" in normalized and "sp" not in normalized and "point" not in normalized:
                names[number] = key
            elif "dev owner" in normalized or "story point" in normalized or re.search(r"\bsp\b", normalized):
                points[number] = key
        pairs: List[tuple[Optional[str], Optional[str], Optional[str]]] = []
        for number in sorted(set(names) | set(points), key=lambda value: int(value)):
            pairs.append((
                number,
                cls._clean_name(cls._get(row, [names[number]]) if number in names else None),
                cls._get(row, [points[number]]) if number in points else None,
            ))
        return pairs

    @staticmethod
    def _clean_name(val: Optional[str]) -> Optional[str]:
        if not val or val.strip().lower() in ("", "nan", "none", "n/a"):
            return None
        return val.strip()

    @staticmethod
    def _parse_sprint_metadata(raw_value: object) -> SprintMetadata:
        """Extract stable Jira sprint metadata without inventing dates."""
        raw = str(raw_value).strip()
        name_match = re.search(r"(?:name=)?([^,\[\]]*Sprint[^,\[\]]*)", raw, re.IGNORECASE)
        name = name_match.group(1).strip() if name_match else raw
        id_match = re.search(r"(?:^|[,;\s])id=(\d+)", raw, re.IGNORECASE)
        date_matches = re.findall(
            r"\d{4}-\d{2}-\d{2}(?:[T ][^,\]]+)?",
            raw,
        )
        start_date = date_matches[0] if date_matches else None
        end_date = date_matches[1] if len(date_matches) > 1 else None
        return SprintMetadata(
            name=name or raw or "Sprint",
            sprint_id=id_match.group(1) if id_match else None,
            start_date=start_date,
            end_date=end_date,
        )

    @staticmethod
    def _parse_sp(val: Optional[str]) -> Optional[float]:
        if val is None:
            return None
        try:
            f = float(val)
            if f < 0:
                return None  # negative SP: caller should warn, we reject the value
            return f
        except (ValueError, TypeError):
            return None
