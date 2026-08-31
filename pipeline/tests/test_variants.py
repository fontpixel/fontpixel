from opf.variants import expand, search_text, variant_map


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


def test_expand_handles_non_adjacent_variants():
    """异体字被普通字符隔开时，整串的另一种写法也要能搜到。

    旧实现只把「其它写法」逐字追加到末尾，于是「俐方體11號」展开成
    「俐方體11號体号」——搜「俐方体11号」反而落空。
    """
    out = expand("俐方體11號")
    assert "俐方體11號" in out
    assert "俐方体11号" in out


def test_expand_renders_whole_alternatives_not_loose_chars():
    out = expand("東雲明朝")
    assert "东云明朝" in out
    assert "東雲明朝" in out


def test_expand_survives_inconsistent_group_order():
    """等价类文件里成员顺序不统一：「驿」组是「驛驿」，「点」组是「点點」。

    所以不能按下标取第 i 个成员——那样只会拼出「文泉驛点阵宋体」这种
    混合体，全繁与全简的写法都落空。
    """
    out = expand("文泉驿点阵宋体")
    assert "文泉驿点阵宋体" in out
    assert "文泉驛點陣宋體" in out

    back = expand("夜照飛點陣字型系列")
    assert "夜照飞点阵字型系列" in back


def test_expand_caps_the_number_of_renderings():
    # 变体字一多，组合数会爆炸；要有上限，且原文始终保留
    long = "东南西北中发白发财万事如意国泰民安风调雨顺"
    out = expand(long)
    assert long in out
    assert len(out.split(" ")) <= 64


def test_search_text_includes_english_names():
    s = search_text("QuanPixel", "全小素", "Poxiao Fonts", "quan-pixel",
                    "", "GalmuriExtended")
    assert "GalmuriExtended" in s
