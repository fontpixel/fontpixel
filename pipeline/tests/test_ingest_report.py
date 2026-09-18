"""The generated import report must not eat the hand-written history below it.

These live outside test_ingest.py on purpose: that module skips wholesale when
the local font collection is absent (as it is in CI), and this behaviour needs
no collection to exercise.
"""

import pytest

from opf.ingest.run import (
    MANUAL_MARKER,
    MANUAL_MARKER_PREFIX,
    IngestReport,
    _write_report,
)

MANIFEST = {"family": [{"slug": "a"}, {"slug": "b"}], "todo": []}


def _report():
    r = IngestReport()
    r.imported = ["a"]
    r.skipped = ["b"]
    return r


def test_new_report_gets_a_marker(tmp_path):
    path = tmp_path / "import-report.md"
    _write_report(_report(), path, MANIFEST)
    text = path.read_text(encoding="utf-8")
    assert "# Import Report" in text
    assert "- a" in text
    assert MANUAL_MARKER in text


def test_rerun_keeps_hand_written_history(tmp_path):
    path = tmp_path / "import-report.md"
    _write_report(_report(), path, MANIFEST)

    history = "\n## 2026-09-01 Some batch\n\nSome family, included for some reason.\n"
    path.write_text(path.read_text(encoding="utf-8") + history, encoding="utf-8")

    later = IngestReport()
    later.imported = ["c"]
    _write_report(later, path, MANIFEST)

    text = path.read_text(encoding="utf-8")
    assert history in text          # the hand-written tail survives verbatim
    assert "- c" in text            # the generated head is refreshed
    assert "- a" not in text        # ...and the stale head is gone
    assert text.count(MANUAL_MARKER) == 1


def test_refuses_to_clobber_a_file_without_the_marker(tmp_path):
    path = tmp_path / "import-report.md"
    handwritten = "# Import Report\n\nEverything here is hand-written.\n"
    path.write_text(handwritten, encoding="utf-8")

    with pytest.raises(ValueError, match="no manual-record marker"):
        _write_report(_report(), path, MANIFEST)

    assert path.read_text(encoding="utf-8") == handwritten


def test_an_older_worded_marker_still_matches(tmp_path):
    """Matching is on the prefix, so rewording the marker cannot strand a report.

    The marker was Chinese until 2026-09-03. A report still carrying that line
    has to keep its hand-written tail rather than trip the refuse-to-clobber
    guard, which would look to the user like the importer breaking.
    """
    path = tmp_path / "import-report.md"
    old_marker = "<!-- opf:manual — 以下为人工维护的收录记录，opf.ingest.run 不会改动 -->"
    assert old_marker.startswith(MANUAL_MARKER_PREFIX)
    history = "\n## Kept\n\nHand-written.\n"
    path.write_text("# stale head\n\n" + old_marker + history, encoding="utf-8")

    _write_report(_report(), path, MANIFEST)

    text = path.read_text(encoding="utf-8")
    assert history in text
    assert old_marker in text       # the file keeps the wording it already had
    assert "stale head" not in text
