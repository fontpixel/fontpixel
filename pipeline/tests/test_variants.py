from fbf.variants import expand, search_text, variant_map


def test_map_covers_simplified_and_traditional():
    m = variant_map()
    assert "東" in m["东"] and "东" in m["東"]
    assert "雲" in m["云"] and "云" in m["雲"]
    assert m["东"] == m["東"]  # 同一等价类


def test_expand_adds_other_forms():
    out = expand("東雲ゴシック")
    assert "東雲" in out  # 原文保留
    assert "东" in out and "云" in out  # 简体写法可被搜到
    back = expand("东云")
    assert "東" in back and "雲" in back


def test_expand_leaves_plain_text_alone():
    assert expand("Galmuri") == "Galmuri"
    assert expand("") == ""
    # 假名与拉丁不受影响
    assert expand("ゴシック") == "ゴシック"


def test_search_text_joins_fields():
    s = search_text("Shinonome Gothic", "東雲ゴシック", "efont")
    assert "Shinonome Gothic" in s
    assert "efont" in s
    assert "东" in s and "云" in s


def test_no_self_duplication():
    # 展开只追加「其它写法」，不重复自身
    out = expand("东")
    assert out.count("东") == 1
    assert "東" in out
