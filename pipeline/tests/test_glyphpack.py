import hashlib
from pathlib import Path

from opf.familymeta import FamilyMeta, resolve_variant
from opf.glyphpack import plan_chunks, read_chunk, write_packs
from opf.parsers.bdf import parse_bdf

FIX = Path(__file__).parent / "fixtures"


def _mini():
    return parse_bdf(FIX / "mini.bdf", "mini")


def _variant(f):
    return resolve_variant(f, FamilyMeta(slug=f.family_slug, name=f.family_slug))


def _dir_hash(d: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(d.rglob("*")):
        if p.is_file():
            h.update(p.name.encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def test_plan_chunks_aligned_and_split():
    f = _mini()
    ranges = plan_chunks(f.glyphs)
    assert ranges == [(0, 256), (27648, 27904)]  # 0x6C00..0x6D00
    for a, b in ranges:
        assert a % 256 == 0 and b % 256 == 0


def test_write_and_read_roundtrip(tmp_path):
    f = _mini()
    manifest = write_packs(f, _variant(f), "mini", tmp_path)
    assert manifest["version"] == 1
    assert manifest["glyphCount"] == 2
    assert len(manifest["ranges"]) == 2
    r0 = manifest["ranges"][0]
    glyphs = read_chunk(tmp_path / r0["file"])
    assert len(glyphs) == 1
    a = glyphs[0]
    assert (a.cp, a.dwidth, a.bbw, a.bbh, a.bbx, a.bby) == (65, 8, 7, 10, 0, 0)
    assert a.rows == f.glyphs[0].rows
    yong = read_chunk(tmp_path / manifest["ranges"][1]["file"])[0]
    assert yong.cp == 27704
    assert yong.rows == f.glyphs[1].rows


def test_core_pack_contains_ascii_only_here(tmp_path):
    f = _mini()
    manifest = write_packs(f, _variant(f), "mini", tmp_path)
    core = read_chunk(tmp_path / manifest["core"]["file"])
    assert [g.cp for g in core] == [65]  # only A is in the core charset for this font
    assert manifest["core"]["glyphs"] == 1


def test_golden_header_bytes(tmp_path):
    import gzip

    f = _mini()
    manifest = write_packs(f, _variant(f), "mini", tmp_path)
    raw = gzip.decompress((tmp_path / manifest["ranges"][0]["file"]).read_bytes())
    assert raw[:8] == b"PFG1\x01\x00\x01\x00"
    assert int.from_bytes(raw[8:12], "little") == 0
    assert int.from_bytes(raw[12:16], "little") == 256


def test_deterministic(tmp_path):
    f = _mini()
    d1 = tmp_path / "a"
    d2 = tmp_path / "b"
    d1.mkdir()
    d2.mkdir()
    write_packs(f, _variant(f), "mini", d1)
    write_packs(f, _variant(f), "mini", d2)
    assert _dir_hash(d1) == _dir_hash(d2)


def test_real_galmuri_chunk_budget(tmp_path):
    f = parse_bdf(FIX / "real-galmuri7.bdf", "galmuri7")
    manifest = write_packs(f, _variant(f), "Galmuri7", tmp_path)
    assert manifest["glyphCount"] == len(f.glyphs)
    assert manifest["core"]["gzBytes"] <= 8192
    for r in manifest["ranges"]:
        assert r["gzBytes"] <= 16384, r
    total = sum(r["glyphs"] for r in manifest["ranges"])
    assert total == len(f.glyphs)
