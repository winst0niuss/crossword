# Panda AI OS — the self-describing factory firmware

The factory firmware line has moved on from the `murphy-26-0526-1.2.16.bin`
("Murphy Reader") image the rest of this repository analyses. The current OTA
release is **Panda AI OS**, and — unlike 1.2.16 — it logs its complete hardware
configuration at boot through `printf`-style format strings that survive in the
binary.

That makes the whole M4 pin map recoverable from the shipped image, and gives an
**independent binary confirmation of every GPIO this repository established by
probing hardware**. It also yields two facts the probes did not cover: an SD
card-detect line, and the bus rates the factory firmware actually runs.

Analysed images:

| Version | Size | SHA-256 |
|---|---:|---|
| `panda-ai-os-2.3.5.bin` (archived here as [`../panda-ai-os-2.3.5.bin`](../panda-ai-os-2.3.5.bin)) | 4,319,904 | `d049bfc8e5d44c8f0be6c8f69855a9b36954e3df053ffecaa5b86dfe449dfebd` |
| `panda-ai-os-2.2.7.bin` (not archived; still served, see below) | 6,009,744 | `089b10973938bdf5f05b8910853a851a1cae586ce68516a50bc4c6871e44c458` |

Both were downloaded from the vendor OTA endpoint and verified against the
`sha256` field of their own manifests. Every constant below was read out of
**2.3.5**; 2.2.7 was disassembled the same way and agrees on all of them.

---

## Where the images come from

`GET https://murphy.pandacat.ai/ota/latest` (2026-08-29):

```json
{
  "version": "2.3.5",
  "firmware_url": "https://murphy.pandacat.ai/firmware/panda-ai-os-2.3.5.bin",
  "firmware_size": 4319904,
  "app_offset": 131072,
  "profile_revision": 1,
  "profile": { "id": "default", "revision": 1,
               "digest": "1c468ae9b4b6019f9fb0830af1f87bb0896d7bab43d70634896270bc2c1d6d65",
               "namespace": "default",
               "sourceRevision": "d98f882c4c9449a6336a8698ab4cc523c5a52687" },
  "product": "murphy-os",
  "board": "mofei",
  "sha256": "d049bfc8e5d44c8f0be6c8f69855a9b36954e3df053ffecaa5b86dfe449dfebd"
}
```

Notes on the endpoint, all checked directly:

- The manifest carries the **whole install recipe**: `app_offset` = `0x20000`,
  the expected size, and a SHA-256 to verify a download against.
- `board` is `"mofei"` with **no model discriminator**, and the response does not
  change for `?model=`, `?device=`, `?board=` or `?size=` query parameters
  (checked on the 2.2.7 manifest). One endpoint serves the whole product line.
- Superseded builds stay reachable at their original
  `/firmware/panda-ai-os-<version>.bin` URL — `2.2.7` still returned HTTP 200 on
  2026-08-29, weeks after `2.3.5` replaced it in the manifest. Only the manifest
  moves on; there is no published index of older versions, so the URL has to be
  known or guessed.

## Image structure (2.3.5)

```
entry=0x403759b0  chip_id=9 (esp32s3)  segments=7
  seg0  DROM  0x3c2a0020  file 0x000020  1,471,120 B   ← strings
  seg1  DRAM  0x3fc9f800  file 0x1672b8     29,624 B
  seg2  IRAM  0x40374000  file 0x16e678      6,560 B
  seg3  IROM  0x42000020  file 0x170020  2,706,432 B   ← application code
  seg4  IRAM  0x403759a0  file 0x404c28    105,896 B
  seg5        0x50000000  file 0x41e9d8         52 B   (RTC slow memory)
  seg6        0x600fe000  file 0x41ea14         96 B
```

Log tags seen at the call sites below: `DISPLAY`, `EPDBUS`, `INPUT`, `STORAGE`,
`POWER`. The platform name printed by the `%s`-prefixed messages is `mofei`.

---

## The self-describing boot log

These format strings exist in `panda-ai-os` 2.2.7 and 2.3.5 and are **absent from
`murphy-26-0526-1.2.16.bin`** (zero matches), which is why this was not visible
in the earlier analysis:

| Format string | What it prints |
|---|---|
| `EPD bus up: SCLK=%d MOSI=%d CS=%d DC=%d RST=%d BUSY=%d @ %d Hz` | display SPI pins and clock |
| `%s panel initialized: logical=%ldx%ld panel=%ldx%ld source=%ld gate=%ld frameBytes=%u logicalStride=%ld panelStride=%ld order=%s rotate180=%d staging=%d` | panel geometry and rotation model |
| `%s touch init SDA=%d SCL=%d INT=%d RST=%d PWR=%d PWR_ON=%d addr=0x%02X freq=%luHz` | touch pins, power rail polarity, I2C address and speed |
| `SD bus pins CLK=%d CMD=%d D0=%d D1=%d D2=%d D3=%d width=%d freq=%d kHz` | SDMMC pins, bus width and clock |
| `SD power/wake GPIO%d=%d` | SD power gate pin and the level it is driven to |
| `SD card detect GPIO%d=%d` | card-detect pin and its level |
| `battery ADC ready gpio=%d unit=%d channel=%d` | battery ADC pin and channel |
| `frontlight ready (cool=%d warm=%d, %lu Hz)` | frontlight channel pins and PWM frequency |

The practical consequence: on a device still running stock Panda AI OS, the pin
map can be read off the USB serial console at boot — no disassembly needed. The
values below are what the disassembler says those calls will print.

---

## Extracted constants

Verified by disassembling each call site (method at the end of this document).
The **"Matches probe"** column refers to [hardware.md](hardware.md), where the
same value was established on real hardware.

### Display bus — `EPD bus up:` @ PC `0x4201d942`

| Signal | GPIO | Matches probe |
|---|---:|---|
| MOSI | 3 | yes |
| SCLK | 4 | yes |
| CS | 5 | yes |
| DC | 6 | yes |
| RST | 7 | yes |
| BUSY | 8 | yes |

The clock argument comes from a variable, not a constant, so the SPI frequency
is not recoverable this way.

### Panel geometry — `%s panel initialized:` @ PC `0x4201c927`

| Field | Value |
|---|---|
| logical | 480 × 800 (portrait) |
| panel | 800 × 480 (landscape) |
| source / gate | 800 / 480 |
| frameBytes | 48,000 (constant `0xbb80` in 2.2.7; computed at run time in 2.3.5) |
| logicalStride / panelStride | 60 / 100 |
| order | `logical-portrait-to-panel-landscape` |
| rotate180 | 0 |

48,000 bytes is 800 × 480 ÷ 8, and the strides are the two row pitches
(480 ÷ 8 = 60, 800 ÷ 8 = 100). The firmware keeps the framebuffer in **logical
portrait** and transposes on the way to the panel, which is the same orientation
model the CrossPoint port ends up needing.

### Touch — `%s touch init SDA=` @ PC `0x4201e446`

| Parameter | Value | Matches probe |
|---|---|---|
| SDA | GPIO13 | yes |
| SCL | GPIO12 | yes |
| INT | GPIO44 | yes |
| RST | `-1` | — (not routed on this board) |
| PWR | GPIO45 | yes |
| PWR_ON | `0` → the rail is **active LOW** | yes |
| I2C address | `0x2E` (`movi a8, 46`) | yes |
| I2C clock | 400,000 Hz (`0x61a80`) | — |

The address is a compile-time constant in 2.3.5; in 2.2.7 it was still loaded
from a configuration struct. This is an independent confirmation of `0x2E` and
of the GPIO45 active-LOW power gate, both of which had been established only by
probing. `RST=-1` says the controller reset line is not wired to a GPIO, so a
reset can only be done through the power rail.

The controller is named directly by neighbouring strings: `FT6336U ready at
0x%02X` and `FT6336U configuration writes failed`. Neither `CHSC6x` (the M3 part)
nor `GT911` appears anywhere in either image.

### SD card — `SD bus pins CLK=` @ PC `0x4201f973`

| Signal | GPIO | Matches probe |
|---|---:|---|
| CLK | 16 | yes |
| CMD | 15 | yes |
| D0 | 17 | yes |
| D1 | 18 | yes |
| D2 | 11 | yes |
| D3 | 14 | yes |

Bus width **4**, clock **20,000 kHz**. The 20 MHz figure is what the factory
firmware configures; the CrossPoint port currently mounts at 400 kHz
([hardware.md](hardware.md)), so the hardware is known to tolerate considerably
more than the port asks of it.

**Power gate** — `SD power/wake GPIO` @ PC `0x4201f8ad`. Immediately before the
log call the firmware executes `gpio_set_level(10, 0)`, then prints `GPIO10=0`.
That is a direct confirmation that **GPIO10 is the SD power enable and is active
LOW**, which cost this repository several probe rounds to establish.

**Card detect** — `SD card detect GPIO` @ PC `0x4201f8e9`. The firmware calls
`gpio_get_level(21)` and prints `GPIO21=<level>`. In 2.2.7 the same pin is
configured just before the read: pin bit mask `0x200000` (bit 21), mode input,
pull-up enabled. **GPIO21 is a card-detect input**, and it is not currently
listed in [hardware.md](hardware.md) — the port does not use it. The active level
is not determined from the binary; only that the line is read as a pulled-up
input.

### Battery — `battery ADC ready gpio=` @ PC `0x4201efe0`

`gpio = 9`, matching the probed GPIO9 ADC. The `unit` and `channel` arguments
come from variables.

### Frontlight — `frontlight ready (cool=` @ PC `0x4201ed53`

`cool = GPIO47`, `warm = GPIO48` — both matching the probe results. In 2.2.7 the
frequency argument is the constant `0x1388` = **5,000 Hz**; in 2.3.5 it comes
from a variable. The CrossPoint port drives these channels at 25 kHz.

### Environment sensors

Not covered elsewhere in this repository. Both images carry probe and
configuration paths for three sensor families, with the bare part names `AHT30`,
`AHT20` and `SHT40` present as strings:

```
%s environment device add failed addr=0x%02X err=%d
AHT20 environment fallback not found addr=0x%02X probe=%d
AHT20 environment fallback detected at 0x%02X status_read=%d status=0x%02X calibrated=%d
AHT20 environment fallback configured at 0x%02X
SHT40 environment candidate addr=0x%02X probe=%d
SHT40 environment sensor configured at 0x%02X
SHT40 environment read CRC mismatch addr=0x%02X
environment one-shot bus init failed err=%d
```

At the AHT20 probe call site (PC `0x4201bf5a`) the address is the constant
`0x38` — the same address the M3's AHT30 sits at. The SHT40 path indexes a
candidate table at vaddr `0x3c344738`, whose first two bytes are `0x44, 0x45`,
the two standard SHT4x addresses.

Which part is actually fitted to an M4 is not decidable from the binary: the
firmware probes for all three and takes whichever answers. Nothing here has been
checked against hardware.

### Panel controller corroboration

The SSD1677 identification made from 1.2.16 holds in this line too. Both images
contain the booster soft-start payload `AE C7 C3 C0 80` (vaddr `0x3c34b718` in
2.3.5, `0x3c4f402c` in 2.2.7) inside a configuration blob that also holds
`df 01` = 479, the gate count for a 480-row panel:

```
8f 8f 8f 8f 8f 01 f7 01 01 df 01 02 ae c7 c3 c0 80 80 03 5a
                              ^^^^^ gate = 479   ^^^^^^^^^^^^^^ booster
```

Neither image contains the strings `SSD1677`, `UC8253`, `GDEQ0426` or any
resolution literal — the controller is only identifiable from its register data.

---

## Reproducing this

The tooling is two small scripts in [`../../tools/`](../../tools/) and the
`objdump` that PlatformIO already installs. Ghidra is not required, and neither
is the Xtensa capstone backend that
[`esp32s3_xtensa_disasm.py`](../../tools/esp32s3_xtensa_disasm.py) needs (the
released capstone 5.x has no `CS_ARCH_XTENSA`).

```bash
# 1. Segment map, plus every call site that references a given string.
python3 tools/find_string_refs.py m4/panda-ai-os-2.3.5.bin \
    "EPD bus up: SCLK=" "SD bus pins CLK=" "%s touch init SDA="

# 2. Disassemble around a PC the previous step reported.
tools/xtensa_ctx.sh m4/panda-ai-os-2.3.5.bin 0x4201f973 90 45
```

Reading the result: logging goes through `call8`, so arguments 0–5 are in
`a10`–`a15` and the rest are on the stack.

| Argument | Location |
|---|---|
| 0 | `a10` — log level |
| 1 | `a11` — tag |
| 2 | `a12` — format string |
| 3, 4, 5 | `a13`, `a14`, `a15` |
| 6, 7, 8, … | `[a1+0]`, `[a1+4]`, `[a1+8]`, … |

The values are placed by `movi` / `movi.n` shortly before the call, often out of
source order and with registers reused between stores. Match arguments by their
**stack offset**, not by the order the lines appear, and be aware that nearby
`s32i` stores may be writing configuration-struct fields rather than call
arguments.

Two things that cost time here:

- A format string beginning with `%s ` must be searched **from its first
  character**. Searching from `panel initialized:` finds the string but not the
  literal that points at it, because the literal holds the address of the `%`.
- `find_string_refs.py` locates `l32r` arithmetically rather than by
  disassembling linearly, because Xtensa instructions are 2 or 3 bytes and code
  is interleaved with literal pools — a linear pass loses sync almost
  immediately. `xtensa_ctx.sh` recovers a consistent start point by walking
  backwards until the instruction chain lands exactly on the requested PC.
