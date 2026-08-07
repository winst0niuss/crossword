#!/usr/bin/env python3
"""Находит все l32r, ссылающиеся на заданный литерал, перебором PC (без дизассемблера).

l32r at, label:  byte0 = (at<<4)|0x1, byte1 = imm&0xff, byte2 = imm>>8
target = ((PC+3) & ~3) + (imm - 0x10000)*4
"""
import struct, sys

data = open('panda227.bin', 'rb').read()
SEGS = [(0x3c370020, 0x000020, 2317916), (0x3fca1b00, 0x235e84, 30152),
        (0x40374000, 0x23d454, 11204), (0x42000020, 0x240020, 3539980),
        (0x40376bc4, 0x5a0434, 110260)]

def foff(va):
    for load, fo, ln in SEGS:
        if load <= va < load + ln:
            return fo + (va - load)
    return None

def find_l32r_to(target_va, seg_load, seg_off, seg_len):
    """Перебираем PC внутри сегмента, проверяем байты l32r."""
    hits = []
    for pc in range(seg_load, seg_load + seg_len - 3):
        base = (pc + 3) & ~3
        delta = target_va - base
        if delta > 0 or delta < -262144 or delta % 4:
            continue
        imm = (delta // 4) + 0x10000
        if not (0 <= imm <= 0xFFFF):
            continue
        o = seg_off + (pc - seg_load)
        b0, b1, b2 = data[o], data[o + 1], data[o + 2]
        if (b0 & 0x0F) == 0x01 and b1 == (imm & 0xFF) and b2 == (imm >> 8):
            hits.append((pc, b0 >> 4))
    return hits

STRINGS = {
    'EPD bus up': 0x3c37d488,
    'panel initialized': 0x3c37ca37,
    'touch init': 0x3c37d81f,
    'SD bus pins': 0x3c37deb0,
    'battery ADC ready': 0x3c37dcc4,
    'FT6336U ready': 0x3c37da60,
}

for name, sva in STRINGS.items():
    # литералы, содержащие адрес строки
    needle = struct.pack('<I', sva)
    lits, p = [], data.find(needle)
    while p != -1:
        for load, fo, ln in SEGS:
            if fo <= p < fo + ln:
                lits.append(load + (p - fo))
        p = data.find(needle, p + 1)
    print(f'\n=== {name}: строка 0x{sva:08x}, литералов {len(lits)}')
    for lit in lits:
        for load, fo, ln in SEGS:
            if load in (0x42000020, 0x40374000, 0x40376bc4):
                for pc, reg in find_l32r_to(lit, load, fo, ln):
                    print(f'    l32r a{reg}, 0x{lit:08x}   @ PC=0x{pc:08x} (file 0x{foff(pc):06x})')
