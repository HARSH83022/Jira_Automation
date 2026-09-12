"""
CSV Data Source — parses Jira CSV exports into row dicts.
"""
from __future__ import annotations

import logging
import csv
from typing import Dict, List, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# Columns that MUST exist (at least one of each group)
REQUIRED_COLUMN_GROUPS = [
    ["Issue key", "Summary"],  # at least one identifier
    ["Status"],                # status is always required
]


class CSVValidationError(Exception):
    pass


class JiraCSVDataSource:
    """Reads a Jira CSV file and returns parsed rows + metadata."""

    def parse(self, file_path: str) -> Tuple[List[dict], List[str], List[str]]:
        """
        Returns:
            rows           – list of row dicts
            detected_cols  – list of column names found
            warnings       – list of warning strings
        
        Supports CSV and TSV (tab-separated values).
        """
        warnings: List[str] = []

        try:
            # Detect the delimiter from the content, not only the extension.
            # Jira exports are commonly renamed to .csv/.txt during download.
            with open(file_path, "r", encoding="utf-8-sig", newline="") as handle:
                sample = handle.read(8192)
            try:
                separator = csv.Sniffer().sniff(sample, delimiters=",\t;|").delimiter
            except csv.Error:
                separator = "\t" if file_path.lower().endswith((".tsv", ".txt")) else ","
            df = pd.read_csv(file_path, sep=separator, encoding="utf-8-sig", low_memory=False)
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, sep=separator, encoding="latin-1", low_memory=False)
        except Exception as exc:
            raise CSVValidationError(f"Unable to read file: {exc}") from exc

        if df.empty:
            raise CSVValidationError("CSV file is empty.")

        # Strip BOM/whitespace from headers so dynamic Jira custom fields are
        # still discoverable when exported by Excel or localized tooling.
        df.columns = [str(column).replace("\ufeff", "").strip() for column in df.columns]
        detected_cols = list(df.columns)
        logger.info("Detected %d columns, %d rows", len(detected_cols), len(df))

        # Validate required columns
        normalized = {str(c).strip().lower() for c in detected_cols}
        has_identifier = bool({"issue key", "summary"} & normalized)
        has_status = "status" in normalized

        if not has_identifier:
            raise CSVValidationError(
                "Unable to process CSV. Required columns 'Issue key' or 'Summary' are missing."
            )
        if not has_status:
            raise CSVValidationError(
                "Unable to process CSV. Required column 'Status' is missing."
            )

        # Replace NaN with None for clean handling
        df = df.where(pd.notnull(df), None)

        rows = df.to_dict(orient="records")

        # Generate warnings for common missing fields
        sp_cols = [
            "Custom field (Dev Owner 1 SP)",
            "Custom field (Dev Owner 2 SP)",
            "Custom field (Story point estimate)",
            "Custom field (Story Points)",
        ]
        dev_cols = ["Custom field (Developer 1)", "Custom field (Developer 2)", "Assignee"]

        missing_sp_count = 0
        missing_dev_count = 0

        for row in rows:
            has_sp = any(
                row.get(c) is not None and str(row.get(c, "")).strip() not in ("", "nan")
                for c in sp_cols
            )
            has_dev = any(
                row.get(c) is not None and str(row.get(c, "")).strip() not in ("", "nan")
                for c in dev_cols
            )
            if not has_sp:
                missing_sp_count += 1
            if not has_dev:
                missing_dev_count += 1

        if missing_sp_count:
            warnings.append(f"⚠ {missing_sp_count} stories do not have Story Point Estimate.")
        if missing_dev_count:
            warnings.append(f"⚠ {missing_dev_count} stories have no developer allocation.")

        logger.info("CSV parsed: %d rows, %d warnings", len(rows), len(warnings))
        return rows, detected_cols, warnings
