"""旧字符集码位 → Unicode 映射(BDF/PCF 共用)。

GL(0x2121 基)与 GR(0xA1A1 基)双字节码通过 |0x80 归一
(对 GR 幂等),再交给对应编解码器。
"""

from __future__ import annotations


def is_unicode_registry(registry: str) -> bool:
    r = registry.lower()
    return r.startswith(("iso10646", "unicode", "ucs"))


def decode_cp(code: int, registry: str, encoding: str,
              warnings: list[str], warned: set[str]) -> int | None:
    reg = registry.lower()
    if is_unicode_registry(reg):
        return code
    if reg.startswith("iso8859"):
        try:
            n = reg.replace("iso8859", "").strip(".-_") or encoding
            codec = f"iso8859_{int(n)}" if n and n != "1" else "latin-1"
            return ord(bytes([code]).decode(codec)) if code >= 0x80 else code
        except Exception:
            return code if code < 0x80 else None
    if reg.startswith("koi8"):
        try:
            return ord(bytes([code]).decode("koi8_r"))
        except Exception:
            return None
    if reg.startswith(("ascii", "iso646")):
        return code if code < 0x80 else None
    if reg.startswith("jisx0201"):
        if code < 0x80:
            return code
        try:
            return ord(bytes([0x8E, code]).decode("euc_jp"))
        except Exception:
            return None

    hi, lo = (code >> 8) & 0xFF, code & 0xFF
    two = bytes([hi | 0x80, lo | 0x80])
    try:
        if reg.startswith("gb2312"):
            return ord(two.decode("gb2312"))
        if reg.startswith(("gbk", "gb18030")):
            return ord(bytes([hi, lo]).decode("gb18030"))
        if reg.startswith("jisx0208"):
            return ord(two.decode("euc_jp"))
        if reg.startswith("jisx0213"):
            return ord(two.decode("euc_jis_2004"))
        if reg.startswith(("ksc5601", "ksx1001")):
            return ord(two.decode("euc_kr"))
        if reg.startswith("big5"):
            return ord(bytes([hi, lo]).decode("big5"))
    except Exception:
        return None
    if reg not in warned:
        warned.add(reg)
        warnings.append(f"unknown charset registry {registry}; unmapped glyphs dropped")
    return None
