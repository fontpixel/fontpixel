

def test_specimen_spreads_across_the_font():
    from opf.samples import specimen

    cps = list(range(0x100, 0x200))
    s = specimen(cps, n=8)
    assert len(s) == 8
    assert s[0] == chr(0x100) and s[-1] < chr(0x200)
    # 等距取样，不是取头 8 个
    assert s != "".join(chr(c) for c in cps[:8])


def test_specimen_skips_control_range_and_handles_small_fonts():
    from opf.samples import specimen

    assert specimen({0x00, 0x1F, 0x41, 0x42}) == "AB"
    assert specimen(set()) == ""


def test_sample_is_broken_only_when_most_chars_are_missing():
    from opf.samples import sample_is_broken

    have = {ord(c) for c in "abc"}
    assert sample_is_broken("xyz", have)          # 全缺
    assert sample_is_broken("ab xy", have)        # 一半缺
    assert not sample_is_broken("abc x", have)    # 只缺 1/4
    assert sample_is_broken("", have)             # 空样例也算不可用
