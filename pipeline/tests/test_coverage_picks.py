"""站点侧的覆盖率短名单与书写系统规则文案，跟管线保持一致。

字表清单和门槛数值分处 TypeScript 与 Python，只能靠这些测试盯住不脱节。
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
    """每种书写系统都要留一张判定它所用的参照字表。

    否则会出现「页面上标着 Traditional Chinese (incomplete)，但筛选器里
    找不到 Big5 常用汉字」的割裂——标签说得出口径，用户却复现不了。
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


@pytest.mark.parametrize("lang", ["zh", "en"])
def test_script_rule_titles_match_the_thresholds(lang: str):
    """chip 上写的百分比必须和实际判定用的门槛一致。

    这两处曾经脱节过：代码把西里尔/希腊的门槛提到 90%，title 里还写着 50%。
    """
    from opf.coverage.engine import (
        KANA_GATE,
        SCRIPT_FULL,
        SCRIPT_REFERENCE_CHARSETS,
        SCRIPT_TARGET,
    )

    full = f"≥ {SCRIPT_FULL * 100:g}%"
    partial = f"{SCRIPT_TARGET * 100:g}–{SCRIPT_FULL * 100:g}%"
    rules = _rules(lang)
    for script in SCRIPT_REFERENCE_CHARSETS:
        assert rules[script].endswith(full), f"{lang}/{script}: {rules[script]}"
        assert rules[f"{script}-partial"].endswith(partial), (
            f"{lang}/{script}-partial: {rules[f'{script}-partial']}"
        )
    # 日文额外要求假名门槛
    assert f"≥ {KANA_GATE * 100:g}%" in rules["ja"]
    assert f"≥ {KANA_GATE * 100:g}%" in rules["ja-partial"]
