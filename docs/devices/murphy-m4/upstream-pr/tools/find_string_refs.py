#!/usr/bin/env python3
"""Locate log format strings in an ESP32-S3 application image and find the
call sites that reference them.

    find_string_refs.py IMAGE                 # header and segment table only
    find_string_refs.py IMAGE "EPD bus up: "  # ... and every call site using it

For each requested string the script reports:

  * the file offset and virtual address of the string itself (DROM);
  * every 4-byte literal in the image whose value is that address;
  * every `l32r` instruction that loads such a literal, with its PC.

Feed the reported PC to xtensa_ctx.sh to read the argument setup around the
call. See m4/findings/panda_ai_os.md for the full workflow and for what the
Murphy M4 factory firmware prints there.
"""

import struct
import sys

CHIP_IDS = {0: "esp32", 2: "esp32s2", 5: "esp32c3", 9: "esp32s3", 12: "esp32c6"}


def load(path):
    """Parse esp_image_header_t + segment headers. Returns (info, segments)."""
    data = open(path, "rb").read()
    magic, seg_count, _spi_mode, _spi_ss, entry = struct.unpack("<BBBBI", data[0:8])
    if magic != 0xE9:
        sys.exit(f"{path}: not an ESP32 application image (magic 0x{magic:02x})")
    chip_id = struct.unpack("<H", data[12:14])[0]

    off = 24  # esp_image_header_t (8) + esp_image_extended_header (16)
    segs = []
    for _ in range(seg_count):
        load_addr, length = struct.unpack("<II", data[off:off + 8])
        off += 8
        segs.append((load_addr, off, length))
        off += length
    return data, {"entry": entry, "chip_id": chip_id}, segs


def kind_of(load_addr):
    if 0x3C000000 <= load_addr < 0x3E000000:
        return "DROM"
    if 0x42000000 <= load_addr < 0x44000000:
        return "IROM"
    if 0x40370000 <= load_addr < 0x403E0000:
        return "IRAM"
    if 0x3FC80000 <= load_addr < 0x3FD00000:
        return "DRAM"
    return "?"


def vaddr_of(segs, file_off):
    for load_addr, off, length in segs:
        if off <= file_off < off + length:
            return load_addr + (file_off - off)
    return None


def find_l32r(data, target, load_addr, off, length):
    """Every `l32r at, target` in one segment, found by trying each PC.

    A linear disassembler loses sync on a raw image (Xtensa instructions are
    2 or 3 bytes and code is interleaved with literal pools), so the encoding
    is checked arithmetically instead:

        l32r at, label:  byte0 = (at << 4) | 0x1
                         byte1 = imm & 0xff
                         byte2 = imm >> 8
        label = ((PC + 3) & ~3) + (imm - 0x10000) * 4

    The literal always sits below the PC, within 256 KiB, 4-byte aligned.
    """
    hits = []
    for pc in range(load_addr, load_addr + length - 3):
        delta = target - ((pc + 3) & ~3)
        if delta > 0 or delta < -262144 or delta % 4:
            continue
        imm = (delta // 4) + 0x10000
        if not 0 <= imm <= 0xFFFF:
            continue
        o = off + (pc - load_addr)
        if (data[o] & 0x0F) == 0x01 and data[o + 1] == (imm & 0xFF) and data[o + 2] == (imm >> 8):
            hits.append((pc, data[o] >> 4))
    return hits


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    data, info, segs = load(path)

    print(f"{path}: entry=0x{info['entry']:08x} "
          f"chip_id={info['chip_id']} ({CHIP_IDS.get(info['chip_id'], '?')}) "
          f"segments={len(segs)}")
    for i, (load_addr, off, length) in enumerate(segs):
        print(f"  seg{i}: load=0x{load_addr:08x} file_off=0x{off:06x} "
              f"len={length:8d}  {kind_of(load_addr)}")

    code_segs = [s for s in segs if kind_of(s[0]) in ("IROM", "IRAM")]

    for pattern in sys.argv[2:]:
        needle = pattern.encode()
        pos = data.find(needle)
        if pos < 0:
            print(f'\n=== "{pattern}": not present in this image')
            continue
        sva = vaddr_of(segs, pos)
        print(f'\n=== "{pattern}"  file=0x{pos:06x}  vaddr=0x{sva:08x}')

        # Literals holding the address of the string.
        lit_needle = struct.pack("<I", sva)
        literals, p = [], data.find(lit_needle)
        while p != -1:
            va = vaddr_of(segs, p)
            if va is not None:
                literals.append(va)
            p = data.find(lit_needle, p + 1)
        if not literals:
            print("    no literal holds this address — the string may be reached "
                  "through a struct field, or the match is mid-string "
                  "(search from the first character, including a leading \"%s \")")
            continue

        for lit in literals:
            print(f"    literal 0x{lit:08x}")
            for load_addr, off, length in code_segs:
                for pc, reg in find_l32r(data, lit, load_addr, off, length):
                    print(f"        l32r a{reg}, 0x{lit:08x}   @ PC=0x{pc:08x}")


if __name__ == "__main__":
    main()
