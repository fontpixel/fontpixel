"""The site-side coverage shortlist and script-rule copy stay in sync with the pipeline.

The charset list and threshold values live separately in TypeScript and Python;
these tests are the only thing keeping them from drifting apart.
"""

import re
from pathlib import Path

import pytest


PICKS = Path(__file__).resolve().parents[2] / "site" / "src" / "lib" / "coveragepicks.ts"


def _picks() -> list[str]:
    if not PICKS.exists():
        pytest.skip("站点目录不在此 checkout 中")
    body = PICKS.read_text(encoding="utf-8")
    body = body[body.index("COVERAGE_PICKS"):]
    return re.findall(r"'([a-z0-9-]+)'", body)


def test_every_script_keeps_at_least_one_reference_charset():
    """Every script must keep at least one reference charset used to determine it.

    Otherwise you get a disconnect like: the page labels something "Traditional
    Chinese (incomplete)", but the filter has no Big5 common-hanzi charset to show
    for it -- the label can state the criterion, but the user can't reproduce it.
    """
    from opf.coverage.engine import SCRIPT_REFERENCE_CHARSETS

    picks = set(_picks())
    missing = [
        script for script, ids in SCRIPT_REFERENCE_CHARSETS.items()
        if not (set(ids) & picks)
    ]
    assert not missing, f"这些书写系统的参照字表一张都没留：{missing}"


def test_picks_are_real_charsets():
    from opf.coverage.charsets import load_charsets

    known = {c.id for c in load_charsets()}
    unknown = [p for p in _picks() if p not in known]
    assert not unknown, f"下拉引用了不存在的字表：{unknown}"


I18N = Path(__file__).resolve().parents[2] / "site" / "src" / "i18n"


def _rules(lang: str) -> dict[str, str]:
    p = I18N / f"{lang}.ts"
    if not p.exists():
        pytest.skip("站点目录不在此 checkout 中")
    body = p.read_text(encoding="utf-8")
    body = body[body.index("scriptRules: {"):]
    body = body[: body.index("},")]
    return dict(re.findall(r"'([\w-]+)':\s*'([^']*)'", body))


@pytest.mark.parametrize("lang", ["zh", "en", "ja", "ko", "fr"])
def test_script_rule_titles_match_the_thresholds(lang: str):
    """The percentage shown on the chip must match the threshold actually used for detection.

    These two have drifted apart before: the code raised the Cyrillic/Greek threshold
    to 90% while the title still said 50%.
    """
    from opf.coverage.engine import (
        CJK_SCRIPTS,
        KANA_GATE,
        SCRIPT_REFERENCE_CHARSETS,
        SCRIPT_TARGET,
        full_threshold,
    )

    rules = _rules(lang)
    # ja/ko/fr phrase some alphabet thresholds in their own style ("90% 以上");
    # the CJK rules, whose threshold differs, are checked in every language.
    scripts = SCRIPT_REFERENCE_CHARSETS if lang in ("zh", "en") else CJK_SCRIPTS
    for script in scripts:
        full = full_threshold(script) * 100
        assert f"≥ {full:g}%" in rules[script], f"{lang}/{script}: {rules[script]}"
        if script != "ja":
            assert rules[f"{script}-partial"].endswith(f"{SCRIPT_TARGET * 100:g}–{full:g}%"), (
                f"{lang}/{script}-partial: {rules[f'{script}-partial']}"
            )
    # Japanese: complete needs every JIS kana; partial needs each kana table
    # at the gate and some level-1 kanji.
    assert f"≥ {KANA_GATE * 100:g}%" in rules["ja-partial"]
    assert f"≥ {SCRIPT_TARGET * 100:g}%" in rules["ja-partial"]
