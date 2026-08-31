from opf.variants import expand, search_text, variant_map


def test_map_covers_simplified_and_traditional():
    m = variant_map()
    assert "東" in m["东"] and "东" in m["東"]
    assert "雲" in m["云"] and "云" in m["雲"]
    assert m["东"] == m["東"]  # same equivalence class


def test_expand_adds_other_forms():
    out = expand("東雲ゴシック")
    assert "東雲" in out  # original text preserved
    assert "东" in out and "云" in out  # simplified spelling is searchable
    back = expand("东云")
    assert "東" in back and "雲" in back


def test_expand_leaves_plain_text_alone():
    assert expand("Galmuri") == "Galmuri"
    assert expand("") == ""
    # kana and Latin are unaffected
    assert expand("ゴシック") == "ゴシック"


def test_search_text_joins_fields():
    s = search_text("Shinonome Gothic", "東雲ゴシック", "efont")
    assert "Shinonome Gothic" in s
    assert "efont" in s
    assert "东" in s and "云" in s


def test_no_self_duplication():
    # expansion only appends "other spellings", it doesn't duplicate the original
    out = expand("东")
    assert out.count("东") == 1
    assert "東" in out


def test_expand_handles_non_adjacent_variants():
    """When variant characters are separated by plain characters, the whole string's alternate spelling must still be searchable.

    The old implementation appended "other spellings" character-by-character to the
    end, so "俐方體11號" expanded to "俐方體11號体号" -- searching for "俐方体11号"
    would then fail to match.
    """
    out = expand("俐方體11號")
    assert "俐方體11號" in out
    assert "俐方体11号" in out


def test_expand_renders_whole_alternatives_not_loose_chars():
    out = expand("東雲明朝")
    assert "东云明朝" in out
    assert "東雲明朝" in out


def test_expand_survives_inconsistent_group_order():
    """Member order is inconsistent across equivalence-class entries: the "驿" group is "驛驿", the "点" group is "点點".

    So picking the i-th member by index doesn't work -- that would only ever
    assemble a mixed form like "文泉驛点阵宋体", missing both the fully-traditional
    and fully-simplified spellings.
    """
    out = expand("文泉驿点阵宋体")
    assert "文泉驿点阵宋体" in out
    assert "文泉驛點陣宋體" in out

    back = expand("夜照飛點陣字型系列")
    assert "夜照飞点阵字型系列" in back


def test_expand_caps_the_number_of_renderings():
    # with many variant characters the combination count explodes; there must be a cap, and the original text is always kept
    long = "东南西北中发白发财万事如意国泰民安风调雨顺"
    out = expand(long)
    assert long in out
    assert len(out.split(" ")) <= 64


def test_search_text_includes_english_names():
    s = search_text("QuanPixel", "全小素", "Poxiao Fonts", "quan-pixel",
                    "", "GalmuriExtended")
    assert "GalmuriExtended" in s
