"""Legacy charset code point → Unicode mapping (shared by BDF/PCF).

GL-based (0x2121 base) and GR-based (0xA1A1 base) double-byte codes are
normalized via |0x80 (a no-op for GR), then handed off to the matching codec.
"""

from __future__ import annotations


def is_unicode_registry(registry: str) -> bool:
    r = registry.lower()
    return r.startswith(("iso10646", "unicode", "ucs"))


# Single-byte charsets: a code point tops out at 0xFF. A larger ENCODING
# appearing in a BDF can only mean the font declared the wrong registry (it's
# actually Unicode-encoded but claims ISO8859) -- in that case pass it
# through as Unicode as-is rather than dropping it as "unmappable". lemon
# lost 839 glyphs this way before this check existed.
_SINGLE_BYTE = ("iso8859", "koi8", "ascii", "iso646")


def decode_cp(code: int, registry: str, encoding: str,
              warnings: list[str], warned: set[str]) -> int | None:
    reg = registry.lower()
    if is_unicode_registry(reg):
        return code
    if code > 0xFF and reg.startswith(_SINGLE_BYTE):
        key = f"{reg}:wide"
        if key not in warned:
            warned.add(key)
            warnings.append(
                f"字体自报 {registry} 单字节字符集,却含 >0xFF 的码位;"
                f"这部分按 Unicode 原样收录"
            )
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

    if reg.startswith("johab"):
        if code < 0x80:
            return code
        try:
            return ord(bytes([(code >> 8) & 0xFF, code & 0xFF]).decode("johab"))
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
