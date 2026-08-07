#!/usr/bin/env python3
"""Разбор ESP32 app image: сегменты, адреса загрузки, поиск строк и ссылок на них."""
import struct, sys

path = sys.argv[1] if len(sys.argv) > 1 else 'panda227.bin'
data = open(path, 'rb').read()

# esp_image_header_t: magic, segment_count, spi_mode, spi_speed/size, entry_addr, ...
magic, seg_count, spi_mode, spi_ss, entry = struct.unpack('<BBBBI', data[0:8])
chip_id = struct.unpack('<H', data[12:14])[0]
print(f'magic=0x{magic:02x} segments={seg_count} entry=0x{entry:08x} chip_id={chip_id} '
      f'({ {0:"esp32",2:"esp32s2",5:"esp32c3",9:"esp32s3"}.get(chip_id,"?") })')

off = 24  # после esp_image_header_t (8) + extended header (16)
segs = []
for i in range(seg_count):
    load_addr, length = struct.unpack('<II', data[off:off + 8])
    off += 8
    segs.append((load_addr, off, length))
    kind = ('DROM' if 0x3c000000 <= load_addr < 0x3e000000 else
            'IROM' if 0x42000000 <= load_addr < 0x44000000 else
            'IRAM' if 0x40370000 <= load_addr < 0x403e0000 else
            'DRAM' if 0x3fc80000 <= load_addr < 0x3fd00000 else '?')
    print(f'  seg{i}: load=0x{load_addr:08x} file_off=0x{off:06x} len={length:8d}  {kind}')
    off += length

def vaddr_of(file_off):
    for load, foff, ln in segs:
        if foff <= file_off < foff + ln:
            return load + (file_off - foff)
    return None

def file_off_of(vaddr):
    for load, foff, ln in segs:
        if load <= vaddr < load + ln:
            return foff + (vaddr - load)
    return None

TARGETS = [b'EPD bus up: SCLK=', b'panel initialized: logical=', b'touch init SDA=',
           b'SD bus pins CLK=', b'battery ADC ready gpio=', b'SD power/wake GPIO',
           b'SD card detect GPIO', b'FT6336U ready at']

print('\n=== строки и ссылки на них ===')
for t in TARGETS:
    pos = data.find(t)
    while pos != -1:
        va = vaddr_of(pos)
        if va is None:
            pos = data.find(t, pos + 1); continue
        print(f'\n"{t.decode()}…"  file=0x{pos:06x}  vaddr=0x{va:08x}')
        # ищем 4-байтовые литералы, равные этому адресу
        needle = struct.pack('<I', va)
        refs, p = [], data.find(needle)
        while p != -1:
            rva = vaddr_of(p)
            if rva is not None:
                refs.append((p, rva))
            p = data.find(needle, p + 1)
        for fo, rv in refs[:8]:
            print(f'    ссылка: literal @ file=0x{fo:06x} vaddr=0x{rv:08x}')
        if not refs:
            print('    ссылок на адрес не найдено (возможен другой способ адресации)')
        break
