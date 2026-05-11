from pathlib import Path

from mint.models import Issue, IssueType, TagDiff
from mint.reporter import format_report


def test_format_report_groups_by_issue_type():
    issues = [
        Issue(Path("/a/01 Song.mp3"), IssueType.MISSING_TPOS,
              [TagDiff("TPOS", "", "1/1")]),
        Issue(Path("/a/02 Song.mp3"), IssueType.MISSING_TPOS,
              [TagDiff("TPOS", "", "1/1")]),
        Issue(Path("/b/06 Feel Good Inc..mp3"), IssueType.TPE1_HAS_FEAT,
              [TagDiff("TPE1", "Gorillaz feat. De La Soul", "Gorillaz")]),
    ]
    out = format_report(issues, scanned=10)
    assert "10 files scanned" in out
    assert "MISSING_TPOS (2" in out
    assert "TPE1_HAS_FEAT (1" in out
    assert "01 Song.mp3" in out
    assert "Feel Good Inc." in out


def test_format_report_empty():
    out = format_report([], scanned=10)
    assert "0 issues" in out
    assert "10 files scanned" in out
