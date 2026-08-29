# Analysis of `panda-ai-os-2.2.7.bin` — the extracted pinout

Date: 2026-08-07. Tools and method are in [tools/README.md](tools/README.md).
Ghidra was not needed: `xtensa-esp32s3-elf-objdump` from PlatformIO was enough.

## Source

```
http://murphy.pandacat.ai/ota/latest
→ {"version":"2.2.7","firmware_url":".../panda-ai-os-2.2.7.bin","firmware_size":6009744,
   "app_offset":131072,"product":"murphy-os","board":"mofei",
   "sha256":"089b10973938bdf5f05b8910853a851a1cae586ce68516a50bc4c6871e44c458"}
```

The size and SHA-256 of the downloaded file match the manifest.

**The server returns the same image for any parameters** — we tried `?model=m4`, `?device=m4`, `?size=4.26`, `?board=e426`: always `2.2.7`, `board: "mofei"`. There is no separate 4.26" build on this endpoint.

## Image structure

```
chip_id=9 (esp32s3)   entry=0x40375cb0   segments=7
  seg0 DROM 0x3c370020  file 0x000020  2,317,916 B
  seg1 DRAM 0x3fca1b00  file 0x235e84     30,152 B
  seg2 IRAM 0x40374000  file 0x23d454     11,204 B
  seg3 IROM 0x42000020  file 0x240020  3,539,980 B   ← all the application code
  seg4 IRAM 0x40376bc4  file 0x5a0434    110,260 B
  seg5      0x50000000  file 0x5bb2f0         52 B   (RTC)
  seg6      0x600fe000  file 0x5bb32c         56 B
```

Log tags: `EPDBUS`, `INPUT`, `STORAGE`, `POWER`. The platform name in the touch log is **`mofei`**.

## Extracted constants

### Display — `EPD bus up:` @ `0x42027f79`

```asm
movi   a8, 8      ; s32i a8, a1, 8    → BUSY
movi.n a8, 7      ; s32i.n a8, a1, 4  → RST
l32r   a12, "EPD bus up: SCLK=%d MOSI=%d CS=%d DC=%d RST=%d BUSY=%d @ %d Hz"
movi.n a8, 6      ; s32i.n a8, a1, 0  → DC
movi.n a15, 5     → CS
movi.n a14, 3     → MOSI
movi.n a13, 4     → SCLK
call8  0x4208a488
```

| Signal | GPIO |
|---|---|
| SCLK | **4** |
| MOSI | **3** |
| CS | **5** |
| DC | **6** |
| RST | **7** |
| BUSY | **8** |

The clock comes from a variable (`a5`), not from a constant.

### Touch — `%s touch init SDA=…` @ `0x42028b65`

| Parameter | Value |
|---|---|
| SDA | **13** |
| SCL | **12** |
| INT | **44** |
| RST | **-1** (not routed) |
| PWR | **45** |
| PWR_ON | **0** → the power line is **active-LOW** |
| addr | from a variable (not a constant) |

The controller is **FT6336U** (`FT6336U ready at 0x%02X` @ `0x42028f1d`); the address is read from a configuration struct. `CHSC6x` and `GT911` do not appear in the image at all.

### Battery — `battery ADC ready gpio=…` @ `0x420299a7`

`gpio = 9`; `unit` and `channel` are substituted from variables.

### SD — `SD bus pins CLK=…` @ `0x4202a051`

Arguments: `CLK=16`, `CMD=15`, `D0=17`, `D1=18`, `D2=11`, `D3=14`, `width=4`, `freq=20000 kHz` (0x4e20).

⚠️ Treat the D0–D3 order with caution: `16, 17, 11, 21` are written into the neighbouring configuration struct as well, and the mapping from the log arguments to the physical lines may be shifted. What is reliable here: the **4-bit bus**, **20 MHz**, and the set of GPIOs involved.

### Panel geometry — `%s panel initialized:` @ `0x42026a2a`

Here the image identifies itself:

```asm
movi a14, 0x1e0    ; 480
movi a15, 0x320    ; 800
l32r a8,  0xbb80   ; 48000
movi a9,  60       ; logicalStride
movi a9', 100      ; panelStride
l32r a13, "mofei"
l32r a12, "%s panel initialized: logical=%ldx%ld panel=%ldx%ld source=%ld gate=%ld
           frameBytes=%u logicalStride=%ld panelStride=%ld order=%s rotate180=%d staging=%d"
```

| Field | Value |
|---|---|
| logical | **480×800** (logical portrait) |
| panel | **800×480** (physical landscape) |
| source / gate | 800 / 480 |
| **frameBytes** | **48,000** = 800 × 480 / 8 |
| logicalStride / panelStride | 60 / 100 |
| order | `logical-portrait-to-panel-landscape` |
| rotate180 / staging | 0 / 1 |

## The main conclusion: the image targets an 800×480 panel, i.e. the M4

`frameBytes = 48000` leaves no alternatives: that is 800×480. On the M3 the frame would be 12,480 bytes (240×416/8). So `panda-ai-os-2.2.7` is built for the **4.26"**, and every constant above is an **M4 pin**.

It also **independently confirms that the M4 resolution is 800×480**, which until now rested on a single owner's report and some ppi arithmetic.

### Why the pins match the M3

The match with the M3 map (display 3/4/5/6/7/8, touch 13/12/44/45, battery 9) is explained by a **shared platform**: one board for both models, differing in panel and case. The SPI pins are simply the link to the panel controller and do not depend on the physical size of the glass.

There is one difference: per the SDK the M3 carries a **CHSC6x** touch controller, while this image has an **FT6336U**, and neither `CHSC6x` nor `GT911` appears in it at all.

| Subsystem | M3 (confirmed on hardware) | M4 (from this image) |
|---|---|---|
| Panel | 240×416, UC8253, 12,480 B frame | **800×480, 48,000 B frame** |
| Display SPI | MOSI=3 SCK=4 CS=5 DC=6 RST=7 BUSY=8 | **the same** |
| Touch | CHSC6x, SDA=13 SCL=12 INT=44, gate 45 active-LOW | **FT6336U**, the same lines |
| Battery | ADC GPIO9 | **GPIO9** |
| SD | 4-bit SDMMC | **4-bit SDMMC, 20 MHz** |

## Reference addresses (so they need not be found again)

The logging function is **`0x4208a488`** (called through `call8`, signature `(level, tag, format, ...)`, level `1` at every site analysed).

| What | String (vaddr) | Literal | `l32r` call PC |
|---|---|---|---|
| `EPD bus up:` | `0x3c37d488` | `0x420028c4` | `0x42027f79` |
| `%s panel initialized:` | `0x3c37ca34` | `0x420027d0` | `0x42026a2a` |
| `%s touch init SDA=` | `0x3c37d81c` | `0x42002974` | `0x42028b65` |
| `SD bus pins CLK=` | `0x3c37deb0` | `0x42002aac` | `0x4202a051` |
| `battery ADC ready gpio=` | `0x3c37dcc4` | `0x420029fc` | `0x420299a7` |
| `FT6336U ready at` | `0x3c37da60` | `0x42002998` | `0x42028f1d` |

Log tags: `EPDBUS` `0x3c37d2bc`, `INPUT` `0x3c37d590`, `STORAGE` `0x3c37de4c`, `POWER` `0x3c37dbe0`, `DISPLAY` `0x3c37c860`. The platform name `mofei` is at `0x3c3780d0`. The scan-order string `logical-portrait-to-panel-landscape` is at `0x3c37cad0`.

## Reproducing this

The analysed images are kept alongside, in [../firmware/](../firmware/), so there is no need to download them again. The commands below are for the case where a newer version from the server is needed:

```bash
# 1. the image (the server may return a newer version — check the sha256 from the manifest)
curl -s http://murphy.pandacat.ai/ota/latest
curl -sL http://murphy.pandacat.ai/firmware/panda-ai-os-2.2.7.bin -o panda227.bin  # already in firmware/

# 2. cut out the IROM segment (offsets from the segment table above)
python3 -c "d=open('panda227.bin','rb').read(); open('irom.bin','wb').write(d[0x240020:0x240020+3539980])"

# 3. then use the scripts in tools/
python3 tools/espimg.py panda227.bin      # segments, strings, literals
python3 tools/findl32r.py                 # call sites
./tools/ctx.sh 0x42027f79 96 24           # disassembly around an address
```

Checksums of the analysed images:

| File | SHA-256 |
|---|---|
| `panda-ai-os-2.2.7.bin` (6,009,744 B) | `089b10973938bdf5f05b8910853a851a1cae586ce68516a50bc4c6871e44c458` |
| `murphy-26-0526-1.2.16.bin` (3,903,024 B) | `3ee3d0a7207a17d49eb47fa60febff8cf4ac2f47bb52d74a1beceb40b8b124ea` |

Both are stored in [../firmware/](../firmware/) together with the factory OEM images: the pandacat server serves only the current version over HTTP, and on an update the old one disappears for good.

## What this means for the port

- **The M4 pin map was obtained before the device arrived.** The board profile can be written now.
- Exactly one thing remains unknown: the **panel controller** (SSD1677 / UC8179 / UC8279). The image
  contains no controller-name strings; it is identified from the init sequence in the code, or by
  runtime auto-detection the way the X4 Pro does it.
- The template profile is `XTEINK_X4_PRO`: the same 800×480 panel, an S3, touch, warm/cool frontlight, SDMMC.
- The **FT6336U** driver will have to be written: `freeink-sdk` does not have one.
- The serial log on first boot (step 2 of the plan) is still useful — as a cross-check, not as the only source.
