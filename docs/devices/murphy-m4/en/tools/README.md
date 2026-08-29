# Tools for analysing the Murphy firmware

Three small scripts that extracted the pinout from the `panda-ai-os-2.2.7.bin` image (see [../firmware-analysis.md](../firmware-analysis.md)). The same scripts apply to a dump of our own device once it arrives.

Ghidra is not needed: PlatformIO already ships `xtensa-esp32s3-elf-objdump` (`~/.platformio/packages/toolchain-xtensa-esp-elf/bin/`).

## `espimg.py` — image structure

```bash
python3 espimg.py panda227.bin
```

Parses the ESP32 application header: chip id, entry point, and every segment with its load address (DROM / IROM / IRAM / DRAM), then finds the requested strings and the literals that reference them.

The list of strings to look for is the `TARGETS` constant inside the file.

## `findl32r.py` — finding references to a string

```bash
python3 findl32r.py
```

A linear disassembler loses sync on a raw binary (Xtensa instructions vary in length and code is interleaved with data), so references are found **arithmetically**: every possible PC is tried, and for each one the bytes are checked for an `l32r` encoding with the required offset.

`l32r at, label`: `byte0 = (at<<4)|0x1`, `byte1 = imm & 0xff`, `byte2 = imm >> 8`, target address `= ((PC+3) & ~3) + (imm - 0x10000) * 4`.

The segment addresses are hard-coded in `SEGS` — update them from the `espimg.py` output when working with a different image.

Important: format strings often begin with `%s ` (the tag). You must search for the address of the **start** of the string, otherwise the reference will not be found — this has already tripped us up.

## `ctx.sh` — disassembly around an address

```bash
./ctx.sh 0x42027f79 96 24     # <PC> [bytes before] [bytes after]
```

Finds a consistent starting point (walking offsets backwards until the instruction chain lands exactly on the PC) and prints the surroundings. It expects an `irom.bin` alongside — the IROM segment cut out of the image using the `espimg.py` data.

## How to read the result

Log calls go through `call8`, so the function arguments sit in `a10`–`a15`, and anything beyond six is on the stack:

| Argument | Where |
|---|---|
| 0 | `a10` — log level |
| 1 | `a11` — tag |
| 2 | `a12` — format string |
| 3, 4, 5 | `a13`, `a14`, `a15` |
| 6, 7, 8, … | `[a1+0]`, `[a1+4]`, `[a1+8]`, … |

The values are put there by `movi` / `movi.n` shortly before the call. Careful: registers are reused, and some `s32i` stores write configuration-struct fields rather than arguments — cross-check by stack offset, not by the order of the lines.

The scripts themselves live in [../../tools/](../../tools/); this page is the English translation of the notes next to them.
