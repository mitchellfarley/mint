from __future__ import annotations

from collections import defaultdict

from mint.models import Issue, IssueType


def format_report(issues: list[Issue], scanned: int) -> str:
    lines: list[str] = []
    lines.append("mint fix — library audit")
    lines.append(f"{scanned} files scanned, {len(issues)} issues found")
    lines.append("")
    if not issues:
        return "\n".join(lines)

    grouped: dict[IssueType, list[Issue]] = defaultdict(list)
    for i in issues:
        grouped[i.issue_type].append(i)

    for issue_type in IssueType:
        bucket = grouped.get(issue_type, [])
        if not bucket:
            continue
        lines.append(f"{issue_type.value} ({len(bucket)} tracks)")
        for issue in bucket:
            diff_strs = [f"{d.field}: {d.current!r} → {d.proposed!r}" for d in issue.diffs]
            lines.append(f"  {issue.path.name}    " + "; ".join(diff_strs))
        lines.append("")

    return "\n".join(lines)
