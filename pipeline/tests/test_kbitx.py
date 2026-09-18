import base64

import pytest

from opf.ingest.kbitx import _decode_bitmap


def decode(raw):
    warnings = []
    bitmap = _decode_bitmap(base64.b64encode(raw).decode(), warnings, 'fixture')
    assert not warnings
    return bitmap


@pytest.mark.parametrize(('opcodes', 'expected'), [
    (bytes([0x21, 0x42]), [0] * 32 + [0x80] * 2),
    (bytes([0x61, 0x01, 0x41]), [0x80] * 32 + [0, 0x80]),
    (bytes([0xA1, 0x80, 0x01, 0x41]), [0x80] * 32 + [0, 0x80]),
    (bytes([0xA1, 0x7F, 0x42]), [0] * 32 + [0x80] * 2),
    (bytes([0xE1] + [0, 255] * 16 + [0x42]), [0, 0x80] * 16 + [0x80] * 2),
])
def test_long_runs_preserve_pixel_positions_in_all_four_modes(opcodes, expected):
    # 34 rows, one column: the last two pixels reveal an incorrect run length.
    assert decode(bytes([34, 1]) + opcodes) == (1, 34, bytes(expected))


def test_short_run_can_end_at_31_pixels():
    assert decode(bytes([32, 1, 0x5F, 0x01])) == (1, 32, bytes([0x80] * 31 + [0]))


def test_muzai_full_block_is_a_solid_8_by_12_rectangle():
    # Actual upstream U+2588 payload: DAhj. 0x63 means 3 * 32 pixels, not 35.
    assert decode(base64.b64decode('DAhj')) == (8, 12, b'\xff' * 12)


@pytest.mark.parametrize(('header', 'size', 'rows'), [
    (bytes([1, 0x82, 1]), (130, 1), b'\xff' * 16 + b'\xc0'),
    (bytes([0x82, 1, 1]), (1, 130), b'\x80' * 130),
])
def test_dimensions_use_unsigned_leb128(header, size, rows):
    assert decode(header + bytes([0x64, 0x42])) == (*size, rows)


def test_incomplete_multibyte_dimension_warns():
    warnings = []
    assert _decode_bitmap('gIA=', warnings, 'broken') is None
    assert warnings == ['broken: truncated bitmap dimension']
