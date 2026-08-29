# Murphy M4 — porting plan and hypothesis matrix

A working document for experiments on the live device. The reference material (hardware, firmware, sources) is in [README.md](README.md) and [sources.md](sources.md).

The principle: **measure first, build second.** Almost everything below is settled within the first hour with the device in hand, and after that the "port" turns into filling in one `BoardProfile` struct.

---

## 1. What is known, and how confidently

| Statement | Confidence | Source |
|---|---|---|
| The MCU is an ESP32-S3 | **high** | the MurphyOS OTA manifest `"chip_family": "ESP32-S3"`, the v1.2.16 image header |
| The panel is 800×480 | **confirmed** | firmware 2.2.7: `frameBytes=48000`, `panel=800x480`, `logical=480x800` |
| The glass is a Good Display GDEQ0426T82 | **high** | that is the 4.26" 800×480 panel from the X4; no other one is in circulation |
| The controller is an SSD1677 or a UC8179/UC8279 | **medium** | all three appear on this panel across different X4/X4 Pro batches |
| Touch is **FT6336U** | **confirmed** | `FT6336U` strings plus the `MofeiTouch` task in both MurphyOS images (1.2.16 and 2.2.7); CHSC6x/GT911 absent |
| SD is 4-bit SDMMC | **high** | the log string `SD bus pins CLK=… CMD=… D0=… D1=… D2=… D3=… width=…` in the 2.2.7 image |
| The frontlight is dual channel (warm+cold) | **medium-high** | users adjust colour temperature → almost certainly two PWM channels |
| Environment sensors are `AHT20` / `SHT40` | medium | strings for both in the 2.2.7 image (the M3 had an AHT30) |
| PSRAM is present | medium | the M3 has 8 MiB; typical for S3 modules of this class |
| 16 MiB flash, no encryption and no secure boot | medium | confirmed on the M3, expected on the M4 |

Everything marked "medium" is settled in a single evening (section 4).

---

## 2. The combination matrix

The axes of uncertainty and what each one means for the work.

### A. The panel controller — the main fork in the road

| Option | Driver in the SDK | What to do |
|---|---|---|
| **SSD1677** | `Ssd1677Driver` | nothing to write: the X4/GDEQ0426T82 config is the default |
| **UC8179** | `Uc8179Driver` | take it as is; on the X4 Pro these two are told apart by auto-detection at boot |
| **UC8279 (800×480)** | `Uc8279X4Driver` | take it as is; **not to be confused** with `Uc8279Driver` for the X3 (792×528) |
| **UC8253** | `Uc8253MurphyDriver` / `Uc8253X3Driver` | practically ruled out: the controller cannot address 800×480 |
| something else | — | worst case: write a driver and extract the LUTs from the dump |

The first three mean the work is already done. The odds of landing in them are high.

### B. Touch — **already identified: FT6336U**

The analysis of the MurphyOS 1.2.16 and 2.2.7 images (2026-08-07) yields `FT6336U` in both: the strings `Mofei FT6336U config failed on SDA=%d SCL=%d addr=0x%02X` and `FT6336U ready at 0x%02X`, plus a `MofeiTouch` task. Neither `CHSC6x` nor `GT911` appears in the images.

| Option | Support | Precedent |
|---|---|---|
| **FT6336U** ← expected | **no driver in the SDK** | Good Display fits it to their panels with touch |
| GT911 | in the SDK | X4 Pro, Sticky, LilyGo |
| CHSC6x | in the SDK | Murphy M3 |

This is the only subsystem that will have to be written from scratch. The FT6336U is a simple I²C controller (an open register map, the FocalTech FT6x36 family), so the task is bounded: reading points, reset/power, and axis mapping. Confirm the address with an I²C scan (`0x38` is typical for the FT6x36; careful: on the M3 an AHT30 sensor sat at `0x38`, so tell them apart by the response, not by the address).

### C. Frontlight

| Option | Support |
|---|---|
| Dual-channel warm/cold PWM | yes: `FrontlightConfig` + `FrontlightManager` (as on the X4 Pro: GPIO8 ch4 / GPIO9 ch5, 10 kHz, 10 bit) |
| Single-channel PWM | yes (de-link, M3, LilyGo) |

### D. SD

| Option | Support |
|---|---|
| 4-bit SDMMC | yes: `FREEINK_SD_SDMMC=1` + `USE_BLOCK_DEVICE_INTERFACE=1` (de-link) |
| 1-bit SDMMC | yes (X4 Pro) |
| SPI | yes (X4, Sticky, M3) |

Separately: on the X4 Pro the card's power line `GPIO5` is **active-LOW** (`SdPins.powerActiveHigh=false`); it is pulsed HIGH→LOW before every mount attempt and held LOW during operation. Holding it HIGH breaks every block read with `0x107`. If the card is "not visible", look for that pin instead of fixing the driver.

The M3 has no such enable: in `MURPHY_M3` (`BoardConfig.h:837`) `powerEnable = PIN_UNASSIGNED`, and `GPIO10` is CS. On top of that the M3's own SD SPI pins (39/13/40) are marked in the SDK as a stale guess: they clash with the confirmed I2S lines (39/40/41/42) and the shared I2C (13), see the comment at `BoardConfig.h:845-847`. The M3 profile cannot be used as an SD precedent.

### E. Buttons

| Option | `InputStyle` | Precedent |
|---|---|---|
| Digital active-low GPIOs | `DigitalButtons` | X4 Pro |
| 3 GPIO keys plus synthesised events | `DigitalFiveKey` | M3 |
| ADC ladder | `XteinkAdcLadder` | X4, de-link |
| Shared OK/power key (click/hold) | `DigitalConfirmPowerHold` | Sticky |

Careful with the power polarity: on most boards the power button is active-LOW (`INPUT_PULLUP`), but on the de-link it is active-HIGH (`INPUT_PULLDOWN`, `InputPins.powerActiveHigh=true`).

### F. Other peripherals (none of them block reading)

RTC (`RX8010` @0x32 on the M3, `BM8563`/`PCF8563` on the X4 Pro/Sticky), a temperature/humidity sensor (`AHT30` @0x38 on the M3, `SHT40` on the Sticky), a battery gauge (`CW2017` @0x63 on the X4 Pro, `BQ27220` @0x55) or a plain ADC with a divider (on the M3, `GPIO9` with a multiplier of 2.0).

---

## 3. Candidate profiles in the SDK

Five ready profiles to build on. Compared by how close they are to the expected M4:

| Profile | MCU | Panel | Touch | Frontlight | SD | Buttons | Closeness to the M4 |
|---|---|---|---|---|---|---|---|
| **`XTEINK_X4_PRO`** | S3 | 800×480, SSD1677 / UC8179 / UC8279 (auto-detect) | GT911 | **warm+cold** | 1-bit SDMMC | digital | **the best template** |
| `DE_LINK` | S3 | 800×480, SSD1677 | none | single channel | 4-bit SDMMC | ADC ladder | very close, but no touch |
| `STICKY` | S3 | 3.97" 800×480, SSD1677 | GT911 | — | SPI | — | the same panel driver |
| `XTEINK_X4` | C3 | 800×480, SSD1677 | none | none | SPI | ADC ladder | the panel reference, but a different MCU |
| `MURPHY_M3` | S3 | 240×416, UC8253 | CHSC6x | single channel | SPI (pins disputed) | `DigitalFiveKey` | a relative by brand, **the wrong panel** |

The key conclusion: **`XTEINK_X4_PRO` is the starting point.** It matches the M4 on the whole feature list (S3, 800×480, touch, warm/cold light, SDMMC, controller auto-detection); the pins will be what differs.

The X4 Pro profile (`BoardConfig.h:1066-1169`) is also well commented: the header splits the fields into CONFIRMED / HIGH / PENDING and names the source of each — an IROM address for the reverse-engineered ones (the pin-init table at `0x420a2240`), a "bit-bang pin sweep" for those verified on hardware. It also states outright what the early assumptions got wrong: the SCLK/MOSI order, the GT911 INT/RST swap, and GPIO1/GPIO2 as an "ADC ladder" (they are power lines). That discipline of annotation is worth copying along with the profile: `DE_LINK` does not have it, and from it you cannot tell what was verified and what was guessed.

One trap when copying: the summary line at `BoardConfig.h:1073` still claims "CONFIRMED … ADC-ladder input style" while the actual `inputStyle` is `DigitalButtons` (`:1085`, confirmed on hardware). The comment went stale after the check; do not inherit it into the M4 profile.

---

## 4. The experiment tree

### Step 0 — before powering on

- [ ] Ask the seller for the **activation code for your UID** (Settings → last entry → Activate Device)
- [ ] Ask corogoo / the seller for the M4 schematics (see README 2.5)
- [ ] `pip3 install esptool`
- [ ] Record the stock firmware version and its lineage (MoFei `EPD426` vs MurphyOS)

### Step 1 — the dump (must come first)

```bash
esptool.py --port /dev/cu.usbmodem* flash_id            # chip, flash size
esptool.py --port /dev/cu.usbmodem* read_flash 0 ALL murphy_m4_dump.bin
```

Check with `esptool.py get_security_info` whether flash encryption or secure boot is enabled.
**Keep the dump private** (NVS holds WiFi passwords); wipe `0x9000`–`0xE000` before publishing.

Success criterion: a 16 MiB file (or whatever `flash_id` reports) that is not all `0xFF`.

### Step 2 — read the stock firmware's boot log ⭐

**The cheapest step in the whole plan, and it should come before any reverse engineering.** The stock Panda AI OS prints its pinout to serial by itself (the format strings were found in the 2.2.7 image):

```bash
~/.platformio/penv/bin/pio device monitor -p /dev/cu.usbmodem* -b 115200
# then reset the device and watch the boot log
```

**The expected values are already known** — extracted from the 2.2.7 image (see [firmware-analysis.md](firmware-analysis.md)): display `SCLK=4 MOSI=3 CS=5 DC=6 RST=7 BUSY=8`, touch `SDA=13 SCL=12 INT=44 RST=-1 PWR=45 PWR_ON=0`, battery `gpio=9`, panel `800×480`, `frameBytes=48000`. The point of this step is to **cross-check**: if they match, the board profile can be written straight away; if they differ, the log's numbers win.

What should appear, and what it gives us:

| String | Gives |
|---|---|
| `EPD bus up: SCLK=… MOSI=… CS=… DC=… RST=… BUSY=… @ … Hz` | the display bus pins and clock |
| `panel initialized: logical=…x… panel=…x… source=… gate=… frameBytes=…` | the **resolution** and frame size |
| `touch init SDA=… SCL=… INT=… RST=… PWR=… PWR_ON=… addr=0x…` | the touch pins plus the power line and its polarity |
| `SD bus pins CLK=… CMD=… D0=… D1=… D2=… D3=… width=… freq=… kHz` | the SDMMC bus (4-bit) |
| `SD card detect GPIO…`, `SD power/wake GPIO…` | card detect and card power |
| `battery ADC ready gpio=… unit=… channel=…` | the battery ADC pin and channel |

If no log appears: USB may be switching between MSC and CDC — try before the device enters user mode, or raise the log level in its settings.

Success here closes most of steps 3 and 4 at once.

### Step 2b — identify the panel controller without touching the device

File work, 10–20 minutes:

```bash
strings -n 6 murphy_m4_dump.bin | grep -iE "ssd1677|uc8179|uc8279|uc8253|gdeq|gdey"
strings -n 6 murphy_m4_dump.bin | grep -iE "gt911|chsc|ft6[0-9]{3}|0x5d|touch"
```

Plus a signature hunt: the framebuffer size (48000 = 800×480/8 versus 12480 on the M3), command `0x61` (TRES) with its gate parameters, and init sequences. The reference is the same method used to extract the OEM waveforms for the M3.

Outcomes:

| What was found | Where next |
|---|---|
| SSD1677 / UC8179 / UC8279 | step 3 with the matching driver — the most likely and easiest path |
| nothing recognisable | compare against `m4/murphy-26-0526-1.2.16.bin` from the Murphy repository (it is a CrossPoint fork, so CrossPoint function names are in it) |
| clearly a different controller | worst case: extract the init plus LUTs from the dump and write a driver |

### Step 3 — I²C scan and GPIO probes

Build a probe sketch (samples: `m3/probes/*.cpp` in the Murphy repository) and flash it. **Only after step 1.**

A trap that cost time on the M3: the bus may sit behind a power gate. If the scan is empty, try the gate candidates by raising each GPIO in turn before concluding "there is no touch controller".

Expected addresses: `0x5D`/`0x14` GT911, `0x2e` CHSC6x, `0x32` RX8010, `0x38` AHT30/FT6x36, `0x51` PCF8563/BM8563, `0x55` BQ27220, `0x63` CW2017.

### Step 4 — display bring-up

Build CrossPoint with a profile copied from `XTEINK_X4_PRO`, substituting the pins found. The goal is any meaningful image.

| Symptom | Most likely cause |
|---|---|
| the screen does not change | wrong CS/DC/RST, or the panel is unpowered (look for powerEnable) |
| it flashes but does not latch | a mismatch between the init and the LUT bank — on the M3 this was a package deal |
| ghosting, dirty background | a LUT with no kick phase / no DC balance (the classic M3 mistake) |
| mirrored or upside down | the mount transform: `ROTATE_180` / mirrorX / mirrorY in the profile |
| artefacts at high clock | lower `displaySpiHz` (20 MHz → 5 MHz) |

### Step 5 — everything else

SD (do not forget the active-low card power) → buttons → touch (the axes and `swapXY`/`flip` are checked by tapping the four corners, as was done on the M3 and X4 Pro) → frontlight → battery → sleep.

### Step 6 — publishing the result

The board profile and driver changes go to `freeink-sdk` (the route the maintainer named explicitly); the dump and hardware findings go to `crosspoint-reader/Murphy`. Everything in between lives in the fork, branch `device/murphy-m4`.

---

## 4.1 Effort estimate

The stages are independent: each produces a result on its own, and it is fine to stop at any of them.

| Stage | What | Estimate |
|---|---|---|
| 0 | Dump + serial log with the pinout + I²C scan, published | an evening |
| 1 | Display bring-up: any meaningful image | days (if the controller is one of the three known ones) — 2–3 weeks (if it is its own) |
| 2 | Buttons + SD → CrossPoint boots and turns pages | about a week |
| 3 | Touch (**the FT6336U driver is written from scratch**), frontlight, battery, sleep | 1–2 weeks |
| 4 | Update quality, fast refresh without ghosting | the longest, drags on |

Stage 0 is worth doing and publishing in any case: it is valuable on its own and raises the chance that people who already have the rest of the plumbing written (Diirge, mr-tbot) join in. **None** of the maintainers has the device.

What removes the main risks: a working CrossPoint fork already runs on this hardware (MurphyOS), a dump makes any brick reversible, and the UI layer can be debugged in the simulator without hardware.

## 4.2 Tooling (macOS)

| Needed | Status | Command |
|---|---|---|
| `esptool` | **not installed** | `pip3 install esptool` |
| PlatformIO | present, 6.1.19 | `~/.platformio/penv/bin/pio` |
| Serial port | no drivers needed | the S3 exposes native USB-CDC → `/dev/cu.usbmodem*` |
| Ghidra + Java | **neither is installed** | needed only for disassembly; the Xtensa plugin is in `tools/` of the Murphy repository |
| Simulator | present | `../crosspoint-simulator`, wired in through `platformio.local.ini` |

A note on USB: if the board carries a CH340/CP2102 bridge instead of native USB, a driver may be needed. If flash encryption is enabled, the dump comes out encrypted (the M3 has none; on the M4 check with `esptool get_security_info`).

## 5. Risks and rollback

| Risk | Mitigation |
|---|---|
| Bricking on a failed flash | the dump from step 1: `esptool.py write_flash 0x0 murphy_m4_dump.bin` |
| The stock OS asks for an activation code after a rollback | the code was requested from the seller in advance (step 0) |
| Flashing the wrong firmware (an M3 build, a C3 image) | do not install the M3 release; upstream has a `chip_id` check (PR #2880), but it is too early to rely on it |
| Damaging the panel with someone else's waveforms | single attempts are safe; do not run wrong LUTs for hours |
| Leaking WiFi passwords from the dump | wipe NVS `0x9000`–`0xE000` before publishing |
| Other people's PRs being rewritten (mr-tbot has already recreated the branch) | pin specific commits instead of following the branch |

---

## 6. What can be done right now, without the device

- [x] **Done 2026-08-07:** both MurphyOS images analysed — `1.2.16` from the Murphy repository and the
      current `panda-ai-os-2.2.7.bin` from the OTA endpoint. Result: touch is `FT6336U`, the sensors are
      `AHT20`/`SHT40`, SD runs over 4-bit SDMMC, and above all the stock firmware **logs the entire
      pinout to serial** (see step 2). The device model is not encoded inside the images; the manifest
      returns `board: "mofei"` with no M3/M4 split.
- [x] **Done 2026-08-07:** `panda-ai-os-2.2.7.bin` disassembled around the log strings and the pin
      constants extracted — see [firmware-analysis.md](firmware-analysis.md). Ghidra was not needed;
      `xtensa-esp32s3-elf-objdump` from PlatformIO was enough. In brief: display
      `SCLK=4 MOSI=3 CS=5 DC=6 RST=7 BUSY=8`, touch `SDA=13 SCL=12 INT=44 PWR=45 (active-LOW)`,
      battery `ADC GPIO9`, SD 4-bit SDMMC at 20 MHz.
      **Caveat:** these values coincide with the M3 map, so this is either an M3 build or a platform
      shared across the line. The very first serial log from our own device settles it.
- [x] **Done 2026-08-09:** read `XTEINK_X4_PRO` (`BoardConfig.h:1066-1169`) and `DE_LINK` (`:854-887`)
      in full, plus the `BoardProfile` definition (`:562-603`) — without it the positional initialisers
      are ambiguous. Conclusion: the X4 Pro fits as a template not only in hardware but structurally —
      it is the only profile that fills in touch with a power rail, a dual-channel frontlight, SDMMC and
      a power latch all at once, i.e. every field the M4 will need. Copy it together with its
      CONFIRMED/HIGH/PENDING annotation and the source reference for each fact.
      Along the way four discrepancies between this plan and the SDK were fixed — §D (SD on the M3),
      §E (`InputStyle` on the M3), and the section 3 table (three-way controller auto-detection, the M3 row).
- [ ] Install `esptool`; optionally Java + Ghidra with the Xtensa plugin (a build is in `tools/` of the
      Murphy repository).
- [ ] Run the UI layer in the simulator (`../crosspoint-simulator`) at 800×480 geometry.
