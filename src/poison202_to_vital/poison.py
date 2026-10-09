"""Read the tagged little-endian P202 layout observed in the supplied exports.

Header: magic, uint16 count, uint16 offset-table-start (=16), eight reserved
bytes, then count absolute uint32 offsets. Each record has a 16-byte name
area, arbitrary-order (four-byte ASCII tag, float32) pairs, and #### terminator.
The name is NUL terminated; bytes after the first NUL are not reliably zero.
"""
from dataclasses import dataclass
import math
from pathlib import Path
import struct

MAX_FILE_BYTES = 32 * 1024 * 1024


class FormatError(ValueError):
    """An unsupported or malformed source export."""


@dataclass(frozen=True)
class Preset:
    name: str
    parameters: dict[str, float]
    index: int
    offset: int
    raw_name: bytes = b""


@dataclass(frozen=True)
class Bank:
    presets: tuple[Preset, ...]
    reserved: bytes


def parse(data: bytes) -> Bank:
    """Validate bounds and framing before reading any parameter values."""
    if len(data) > MAX_FILE_BYTES:
        raise FormatError("P202 file exceeds the 32 MiB input limit")
    if len(data) < 20 or data[:4] != b"P202":
        raise FormatError("Not a supported P202 file: missing P202 header")
    count, table_start = struct.unpack_from("<HH", data, 4)
    if not 1 <= count <= 300:
        raise FormatError(f"Invalid preset count {count}; expected 1..300")
    if table_start != 16:
        raise FormatError(f"Unsupported P202 header layout: table starts at {table_start}")
    table_end = table_start + count * 4
    if table_end > len(data):
        raise FormatError("Truncated P202 offset table")
    offsets = struct.unpack_from(f"<{count}I", data, table_start)
    if offsets[0] != table_end or any(a >= b for a, b in zip(offsets, offsets[1:])):
        raise FormatError("P202 offsets must be increasing and start after the offset table")
    if offsets[-1] >= len(data):
        raise FormatError("P202 record offset is outside the file")
    presets = []
    for index, (start, end) in enumerate(zip(offsets, (*offsets[1:], len(data))), 1):
        record = data[start:end]
        if len(record) < 28 or (len(record) - 20) % 8 or record[-4:] != b"####":
            raise FormatError(f"Preset {index}: truncated or invalid record framing")
        raw_name = record[:16]
        name_bytes = raw_name.split(b"\0", 1)[0]
        try:
            name = name_bytes.decode("utf-8")
        except UnicodeDecodeError:
            name = name_bytes.decode("latin-1")
        name = name.strip() or f"Preset {index:03d}"
        parameters = {}
        for pos in range(16, len(record) - 4, 8):
            tag_bytes = record[pos:pos + 4]
            if any(c < 33 or c > 126 for c in tag_bytes):
                raise FormatError(f"Preset {index}: non-ASCII parameter tag at byte {start + pos}")
            tag = tag_bytes.decode("ascii")
            value = struct.unpack_from("<f", record, pos + 4)[0]
            if not math.isfinite(value):
                raise FormatError(f"Preset {index}: non-finite value for {tag}")
            if tag in parameters:
                raise FormatError(f"Preset {index}: duplicate parameter tag {tag}")
            parameters[tag] = value
        presets.append(Preset(name, parameters, index, start, raw_name))
    return Bank(tuple(presets), data[8:16])


def load(path: str | Path) -> Bank:
    with Path(path).open("rb") as source:
        data = source.read(MAX_FILE_BYTES + 1)
    return parse(data)
