from pathlib import Path

from opf.mergesubsets import group_files, merge

FIX = Path(__file__).parent / "fixtures"


def _p(*names):
    return [Path(n) for n in names]


def test_groups_charset_subsets_under_the_main_file():
    got = group_files(_p(
        "mplus_j10r.bdf", "mplus_j10r-iso-W5.bdf", "mplus_j10r-jisx0201.bdf",
        "mplus_j10b.bdf", "mplus_j10b-iso.bdf",
    ))
    assert {k.name: [v.name for v in vs] for k, vs in got.items()} == {
        "mplus_j10b.bdf": ["mplus_j10b-iso.bdf"],
        "mplus_j10r.bdf": ["mplus_j10r-iso-W5.bdf", "mplus_j10r-jisx0201.bdf"],
    }


def test_longest_stem_wins():
    """a-b-c should group under a-b, not a."""
    got = group_files(_p("a.bdf", "a-b.bdf", "a-b-c.bdf"))
    assert {k.name: [v.name for v in vs] for k, vs in got.items()} == {
        "a.bdf": ["a-b-c.bdf", "a-b.bdf"],
    }


def test_unrelated_names_are_not_grouped():
    got = group_files(_p("alpha.bdf", "alphabet.bdf"))
    assert sorted(k.name for k in got) == ["alpha.bdf", "alphabet.bdf"]


def test_merge_adds_only_missing_codepoints():
    from opf.parsers.bdf import parse_bdf

    base = parse_bdf(FIX / "mini.bdf", "mini")
    before = {g.cp for g in base.glyphs}
    other = parse_bdf(FIX / "mini.bdf", "mini")
    merged, notes, rejected = merge(base, [other])
    assert {g.cp for g in merged.glyphs} == before  # all duplicates, none added
    assert "并入 0 个字形" in notes[0]
    assert rejected == []


def test_merge_refuses_other_pixel_sizes_but_hands_them_back():
    """Mismatched sizes can't be merged, but must be handed back to the caller separately -- glyphs must not be lost."""
    from opf.parsers.bdf import parse_bdf

    base = parse_bdf(FIX / "mini.bdf", "mini")
    other = parse_bdf(FIX / "mini.bdf", "mini")
    other.pixel_size = base.pixel_size + 2
    other.file_name = "other.bdf"
    _, notes, rejected = merge(base, [other])
    assert "未合并" in notes[0]
    assert [f.file_name for f in rejected] == ["other.bdf"]


def test_merge_expands_ascent_to_fit_every_part():
    """Differing ascent/descent at the literal level doesn't block merging -- the max is taken so every glyph fits."""
    from opf.parsers.bdf import parse_bdf

    base = parse_bdf(FIX / "mini.bdf", "mini")
    other = parse_bdf(FIX / "mini.bdf", "mini")
    other.glyphs = [g for g in other.glyphs if g.cp == 0x41]
    other.glyphs[0].cp = 0x42  # fabricate a codepoint base doesn't have
    other.ascent = base.ascent + 5
    merged, _, rejected = merge(base, [other])
    assert rejected == []
    assert merged.ascent == base.ascent  # base has been modified in place to the max value
    assert 0x42 in {g.cp for g in merged.glyphs}
