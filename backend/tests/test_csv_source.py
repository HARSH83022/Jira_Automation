"""Tests for CSV data source validation."""
import os
import tempfile
import pytest
from app.datasources.csv_source import JiraCSVDataSource, CSVValidationError


def _write_csv(content: str) -> str:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
    tmp.write(content)
    tmp.close()
    return tmp.name


def test_valid_csv_parses():
    path = _write_csv(
        "Issue key,Summary,Status,Assignee\n"
        "X-1,Story 1,Done/ Live,Raj Shinde\n"
    )
    try:
        rows, cols, warnings = JiraCSVDataSource().parse(path)
        assert len(rows) == 1
        assert "Issue key" in cols
    finally:
        os.unlink(path)


def test_missing_status_raises():
    path = _write_csv("Issue key,Summary\nX-1,Story 1\n")
    try:
        with pytest.raises(CSVValidationError, match="Status"):
            JiraCSVDataSource().parse(path)
    finally:
        os.unlink(path)


def test_missing_identifier_raises():
    path = _write_csv("Status,Assignee\nDone/ Live,Raj Shinde\n")
    try:
        with pytest.raises(CSVValidationError):
            JiraCSVDataSource().parse(path)
    finally:
        os.unlink(path)


def test_empty_csv_raises():
    path = _write_csv("Issue key,Status\n")
    try:
        with pytest.raises(CSVValidationError, match="empty"):
            JiraCSVDataSource().parse(path)
    finally:
        os.unlink(path)


def test_missing_sp_warning():
    path = _write_csv(
        "Issue key,Summary,Status\n"
        "X-1,Story 1,To Do\n"
        "X-2,Story 2,Done/ Live\n"
    )
    try:
        _, _, warnings = JiraCSVDataSource().parse(path)
        assert any("Story Point" in w for w in warnings)
    finally:
        os.unlink(path)


def test_delimiter_is_detected_from_content():
    path = _write_csv(
        "Issue key;Summary;Status\n"
        "X-1;Story 1;Done/ Live\n"
    )
    try:
        rows, cols, _ = JiraCSVDataSource().parse(path)
        assert rows[0]["Issue key"] == "X-1"
        assert cols == ["Issue key", "Summary", "Status"]
    finally:
        os.unlink(path)
