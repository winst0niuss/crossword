# Murphy M4 — CrossPoint Reader port

*English translation of the notes in [`docs/devices/murphy-m4/`](../README.md); the Russian files remain the working originals.*

Working notes on porting the firmware to the **Murphy** e-reader (also sold as Mofei / 摩菲, and listed by HamGeek). The target device is the **M4 4.26"**, 32 GB / Long battery variant, ordered from AliExpress and in transit.

Status: **gathering information**. The device has not arrived yet, so there are no dumps from our own unit.
Everything below comes from public sources (see [sources.md](sources.md)), not from our own measurements.

---

## 0. The essentials, in two paragraphs

**The M4 is not "another X4".** It is an ESP32-S3 (not the C3 of the Xteink X4/X3), with a touchscreen, a frontlight, USB-C with OTG, and SD. The stock firmware from pandacat.ai ("MurphyOS" / Murphy Reader v1.2.x) **is itself a CrossPoint fork**: the CrossPoint team decompiled the image and found a `CrossPointWebServer` class, the XOR key from `WifiCredentialStore.cpp`, and OPDS / KOReader Sync / Calibre Wireless strings inside it. So the hardware is demonstrably capable of running CrossPoint; the only open question is the board profile.

**There is no official M4 port yet.** There is a working port for the **M3 (3.7")** and a reverse-engineering repository, [crosspoint-reader/Murphy](https://github.com/crosspoint-reader/Murphy). For the M4 that repository only analyses the OTA image; **nobody has taken a raw flash dump yet**, and that is the first thing worth doing with the device once it arrives.

---

## 1. The naming confusion (read before buying or flashing)

Sellers and users apply the same name to different devices. The classification the CrossPoint repository follows:

| What is meant | Screen | Actual generation | Stock firmware |
|---|---|---|---|
| "Murphy 3.7", "Murphy M4 3.7", "Murphy 3" | 3.7", 416×240 | **M3** | OEM MoFei/corogoo (`touch`) |
| "Murphy M4 4.26", "Murphy 4.2" | 4.26" | **M4** | MoFei `EPD426` **or** MurphyOS (pandacat) |

Traps:

- In the CrossPoint repository the file for the **4.26"** panel (`mofei-corogoo-EPD426-v1.bin`) sits in `m3/oem_firmware/` — as the "big brother" of the OEM firmware, not because it belongs to the M3.
- Flashing 3.7" firmware onto a 4.26" (or the other way round) bricks the device; Reddit has this happening over and over.
- Recovery from a brick worked for people through the web flasher at `crosspointreader.com/#flash-tools` with a custom `.bin`: hold power, press reset, release reset, keep holding power for the whole flash. The device profile was found by trial and error — on the 3.7" some succeeded with **Xteink X4**, others only with **X4 Pro**. No confirmed recipe for the M4 appears in any of the reports.

---

## 2. Murphy M4 (4.26") — the target device

### 2.1 Hardware

| Parameter | Value | Confidence |
|---|---|---|
| MCU | **ESP32-S3** | confirmed: OTA manifest `"chip_family": "ESP32-S3"`, v1.2.16 image header |
| PSRAM | not confirmed (the M3 has 8 MiB) | ? — needs a dump |
| Flash | not confirmed (the M3 has 16 MiB) | ? — needs a dump |
| Screen | 4.26" e-ink, monochrome, **~220 ppi** (Xteink X4 class) | per the seller and users |
| Resolution | **800×480** | **confirmed**: firmware 2.2.7 has `frameBytes=48000`, `panel=800x480` (see [firmware-analysis.md](firmware-analysis.md)) |
| Panel controller | unknown (SSD1677 / UC8179 / UC8279) | the only thing left to establish |
| Frontlight | present, with brightness **and colour temperature** control | confirmed by user reports |
| Touch | **FT6336U**, `SDA=13 SCL=12 INT=44`, power on `GPIO45`, active-LOW | from the 2.2.7 firmware analysis |
| Buttons | physical buttons present (including power and a recessed reset) | confirmed; the page-turn layout is not documented |
| Storage | microSD (16/32 GB bundled), **expandable** | confirmed |
| USB | **USB-C with OTG**: in "file transfer" mode the SD card appears as a flash drive | confirmed |
| Wi-Fi | present, including an access point plus a built-in web server (192.168.8.8) | confirmed |
| Bluetooth / audio | claimed for the Murphy line (wav/aac/mp3/flac on the 3.7") | nobody reporting on the M4 has tested it |
| RTC / clock | present, lock screen with a clock, alarm | confirmed |
| Sensors | temperature and humidity | claimed by the seller |
| Battery | 2000–2500 mAh claimed; some reports doubt the figure | disputed |
| Case | 3D printed (a CNC option is +$2); unlike the X4 there is **no magnet** | confirmed |
| Size/weight | roughly the Xteink X4, about 1.5 mm thicker and slightly heavier | per owners of both |
| Price | $54–90 depending on seller and configuration | — |

### 2.2 The firmware that exists for the M4

1. **OEM MoFei / corogoo — `EPD426-v1`.** Branch `firmware/EPD426-v1` at
   <https://gitee.com/corogoo/3.7-inch-ink-screen-reader>; the people reporting took v626 and v628 from there.
   Later builds of the same stock line (v631, v635, v637) are distributed through
   `murphy.pandacat.ai/tools/rollback` instead. From roughly v621 onwards EPUB rendering was fixed
   (before that you had to convert to .txt with Calibre), images in EPUB appeared, and
   `.ttf`/`.otf` files load directly (drop them in `/font`, no conversion).
2. **MurphyOS / "Murphy Reader"** — <https://murphy.pandacat.ai/>. This is the **CrossPoint fork**
   discussed below; the analysed version is v1.2.16. The stock build on their rollback page is free,
   while "Panda OS" (version 2.1 in the reports) is paid, around $19. Opinions on the paid one are
   mixed: complaints about broken EPUB rendering and about not finding how to turn the frontlight on.
3. **A CrossPoint port** — none official. The "ported Crosspoint" builds mentioned in reports work
   badly (lag, freezes); the reporters rolled back to stock.

⚠️ **Activation code.** When reflashing or recovering the stock OS the device asks for an activation code tied to its UID (the UID is in the last settings entry, "Activate Device"). The AliExpress seller issues the code on request once you give them the UID. It is worth **requesting the code up front**, before any firmware experiments.

### 2.3 MurphyOS = a CrossPoint fork (the key fact for the port)

The analysis of `murphy-26-0526-1.2.16.bin` (3,903,024 bytes, ESP-IDF v5.5.4, built 2026-03-31,
`app_offset` 131072) in [m4/findings/murphy_reader_code_reuse.md](https://github.com/crosspoint-reader/Murphy/blob/main/m4/findings/murphy_reader_code_reuse.md)
found the following in the binary:

- the string `CrossPointWebServer` in the activity list (the class name from `src/network/CrossPointWebServer.cpp`);
- the obfuscation XOR key from `WifiCredentialStore.cpp`;
- log strings whose wording appears only in the CrossPoint repository;
- OPDS / KOReader Sync / Calibre Wireless features that the base MoFei firmware does not have.

None of that is in the OEM MoFei image, so the fork happened on top of CrossPoint.

The practical conclusion: **CrossPoint will certainly run on this hardware**, and MurphyOS is a ready reference for the pins and the display driver. The repository holds the OTA image itself plus a Ghidra inventory and string-match tables (unlike the M3, the Ghidra project for the M4 is not published).

A separate find: MurphyOS implements **runtime `.ttf` rendering**, analysed in
[m4/findings/murphy_reader_ttf_fonts.md](https://github.com/crosspoint-reader/Murphy/blob/main/m4/findings/murphy_reader_ttf_fonts.md),
and there is a draft for porting it upstream into CrossPoint (`porting_ttf_to_crosspoint.md`).

### 2.3.1 Analysis of the MurphyOS images (2026-08-07, our own check)

We downloaded and inspected both images. **A caveat about `murphy-26-0526-1.2.16.bin`:** the "26" in the name is the year (`build_date: 2026-05-26`), not the 4.26" panel. The image carries no model marker: across 23,789 strings there is no `SSD1677`/`UC8179`/`UC8253`, no `800x480`/`416x240`, no `M3`/`M4`, and no `E426`/`E037`. The only identifiers are `Murphy version: 1.2.16` and `PandaR-ESP32-1.2.16`. In other words, "this is the M4 firmware" is a claim by the Murphy repository authors, not a property of the file. By contrast, the **stock** line puts the model in the filename: `V169_E426_TOUCH` (4.26") versus `firmware_V532_E037_TOUCH.bin` (3.7").

**The current version is 2.2.7, not 1.2.16.** The OTA endpoint `murphy.pandacat.ai/ota/latest` returns:

```json
{"version":"2.2.7","firmware_url":".../panda-ai-os-2.2.7.bin","firmware_size":6009744,
 "app_offset":131072,"product":"murphy-os","board":"mofei",
 "sha256":"089b10973938bdf5f05b8910853a851a1cae586ce68516a50bc4c6871e44c458"}
```

`board: "mofei"` — **with no split by model**, so Panda AI OS looks like a single image for the whole line. The file has been downloaded and its checksum matches.

**What the 2.2.7 analysis gives us — the most valuable part of the whole investigation:**

- **Touch is `FT6336U`.** Strings `Mofei FT6336U config failed on SDA=%d SCL=%d addr=0x%02X`,
  `FT6336U ready at 0x%02X`, and a `MofeiTouch` task. Neither `CHSC6x` (as on the M3) nor `GT911`
  appears in the image. The same FT6336U is present in 1.2.16 as well. Good Display specifies exactly
  this part for its panels with touch. **freeink-sdk has no FT6336U driver** — that one will have to be written.
- **Environment sensors — `AHT20` and/or `SHT40`** (the M3 had an AHT30).
- **The stock firmware prints the entire pinout to serial itself.** The format strings:

  | String in the image | What it prints |
  |---|---|
  | `EPD bus up: SCLK=%d MOSI=%d CS=%d DC=%d RST=%d BUSY=%d @ %d Hz` | display bus pins and clock |
  | `%s panel initialized: logical=%ldx%ld panel=%ldx%ld source=%ld gate=%ld frameBytes=%u …` | **panel geometry** and frame size |
  | `%s touch init SDA=%d SCL=%d INT=%d RST=%d PWR=%d PWR_ON=%d addr=0x%02X freq=%luHz` | touch pins, the power line and its polarity |
  | `SD bus pins CLK=%d CMD=%d D0=%d D1=%d D2=%d D3=%d width=%d freq=%d kHz` | the SDMMC bus (so 4-bit SDMMC) |
  | `SD card detect GPIO%d=%d`, `SD power/wake GPIO%d=%d` | card detect and card power |
  | `battery ADC ready gpio=%d unit=%d channel=%d` | battery ADC pin and channel |

**Practical conclusion:** the M4 pin map and resolution can be had **without reverse engineering** — plug in USB and read the stock firmware's boot log. That is the first thing to do after the dump.

### 2.4 What already exists for the M4, and what is missing

| Have | Missing |
|---|---|
| MurphyOS v1.2.16 OTA image + Ghidra inventory, string match against CrossPoint | a raw flash dump (nobody has taken one) |
| Extracted web-UI assets (`HomePage.html`, `FilesPage.html`, …) | the M4 pin map |
| Proven MurphyOS ↔ CrossPoint lineage | confirmed resolution and panel controller |
| Analysis of the native `.ttf` handling | a board profile and a port |

**No maintainer has the device.** Diirge (CrossPoint Team) wrote that he needs an M4 in hand to do the port; Justin Mitchell confirmed the same on 2026-08-06 (see 2.6). So whoever takes the first M4 dump closes that gap for everyone.

### 2.5 The manufacturer is officially open to developers

In issue [crosspoint-reader#2311](https://github.com/crosspoint-reader/crosspoint-reader/issues/2311)
(2026-06-10) the Murphy development team, posting from the **corogoo** account, stated outright that:

- the Murphy M4 and Murphy 3.7 are **fully open to developers**;
- they **provide complete hardware schematics** and display-driver material;
- features such as plugins and OPDS seen in reviews are **not their official firmware** but community
  CrossPoint ports (so pandacat/MurphyOS is a third party, not the manufacturer);
- they want to work with the CrossPoint team.

The issue was closed by Justin Mitchell (`itsthisjustin`, CrossPoint maintainer and author of the Murphy reverse-engineering repository) with a note that he replied by email.

**Practical conclusion:** the M4 schematics can simply be requested from the manufacturer through the seller or through corogoo's contacts — cheaper than recovering the pinout with a multimeter.

### 2.6 The CrossPoint maintainer's reply (2026-08-06)

In the same issue I asked whether Justin Mitchell had received the material from corogoo by email and whether it could be shared ([comment](https://github.com/crosspoint-reader/crosspoint-reader/issues/2311#issuecomment-5208195057)). The reply:

> I unfortunately don't have the hardware yet but I do know there's a fork somewhere here that
> someone has working. Porting the sdk pieces over here would be ideal

What follows from that:

1. **The maintainer has no schematics** — he still has no device, and he does not offer the corogoo
   material. The only channel for schematics is the manufacturer or the seller.
2. **"A fork somewhere that someone has working"** — he gave no specifics, and no such fork exists
   publicly. Checked: a GitHub code search (`MurphyM4`, `murphy_m4`, `env:murphy_m4`) returns nothing;
   `Uc8253Murphy` appears only as the M3 driver (the SDK itself and vendored copies of it); across the
   39 forks of `freeink-sdk` and the `community-sdk` / `Murphy` branches the only relevant branch is
   `feat-support-for-m3`. Two plausible explanations: either he means **MurphyOS by pandacat** (which
   does run on the M4, but its sources are closed and MIT does not oblige anyone to open them), or he
   is thinking of **mr-tbot's fork**, which is about the M3.
3. **Where the result should go:** "porting the sdk pieces over here" — that is, the board profile and
   the panel driver are expected in `freeink-sdk`, by the same route the M3 took in PR #25.

---

## 3. Murphy M3 (3.7") — the neighbour in the family

Useful as a ready-made base: on the M3 CrossPoint **does not merely boot, it has been taken to a working firmware with published binaries**, and nearly the whole method (tooling, Ghidra, the analysis scheme, the board profile) is reusable for the M4.

### 3.1 Hardware (confirmed by a dump and by probing a live device)

- MCU: **ESP32-S3 (QFN56) rev v0.2**, dual core at 240 MHz, an ESP32-S3R8 class module:
  **8 MiB PSRAM**, **16 MiB flash** (quad-SPI, GigaDevice).
- USB: **native USB-Serial/JTAG**, `303a:1001` — no separate bridge needed.
- **Neither flash encryption nor secure boot** — the device dumps and reflashes freely.
  The same is most likely true of the M4, and that is what makes the "dump first" plan workable.
- Panel: Good Display **`GDEY037T03-FT21`**, controller **UC8253**, **240×416**, monochrome (~130 ppi).
  Framebuffer 240/8×416 = **12,480 bytes**. Greyscale **does not work** — the VSH/VSL rails are
  asymmetric, and the attempt at 4 grey levels was abandoned.
- A close hardware relative: the Elecrow CrowPanel ESP32 3.7" E-paper HMI.
- I²C peripherals (confirmed by probing in SDK PR #25):

  | Address | Device |
  |---|---|
  | `0x10` | audio codec **ES8388** |
  | `0x2e` | touch **CHSC6x** |
  | `0x32` | RTC **RX8010** (ticking; no driver in the SDK) |
  | `0x38` | temperature/humidity sensor **AHT30** (no driver in the SDK) |

- Charging: **TP4054**; the `CHRG` output is not routed out, so "charging" is detected indirectly
  from the USB-Serial/JTAG SOF counter (`freeink::usbHostPresent()`).
- LittleFS + SD/MMC.

### 3.2 M3 pin map

| Function | Pins |
|---|---|
| Display bus (bit-banged UC8253) | `MOSI=3 SCK=4 CS=5 DC=6 RST=7 BUSY=8` (BUSY ready-high) |
| Frontlight | `GPIO48`, active-high PWM, 25 kHz |
| Side buttons | top `GPIO1`, middle `GPIO2`, bottom `GPIO0` (active-low) |
| SD (4-bit SDMMC) | `CLK=16 CMD=17 D0=15 D1=14 D2=21 D3=18`; power on `GPIO10`, **active-low** |
| Touch (I²C) | `SDA=13 SCL=12`, addr `0x2e`, INT `GPIO44` active-low |
| Gate for the whole I²C bus | `GPIO43` — must be raised before any I²C access |
| Power gate for touch and the ES8388 | `GPIO45`, **active-low** |
| Battery (ADC) | `GPIO9`, divider 680 kΩ / 680 kΩ → multiplier **2.0** |
| Power LED | `GPIO41` |

Rakes already stepped on (from SDK PR #25):

- public CrowPanel maps list `GPIO48` as EPD BUSY — **on the Murphy that pin is the frontlight**;
- `GPIO45` was recorded in early notes as the touch reset — **that is wrong**, it is the power gate,
  and in the wrong state both the touch controller and the codec vanish from the bus;
- `GPIO10` (SD power) is active-low: the "obvious" logic leaves the card unpowered and the slot
  looks dead;
- the CHSC6x **cannot handle repeated-start** — reads must be separated by a stop;
- the battery divider multiplier of 3.03 (which was in the profile) reported 6.3 V on a charging LiPo;
- `GPIO0` is simultaneously a strap pin, the confirm button and the power button, so the hold-to-sleep
  threshold was raised to 1500 ms.

### 3.3 M3 flash layout (16 MiB, ESP-IDF OTA)

| Partition | Offset | Size |
|---|---:|---:|
| `nvs` | `0x009000` | `0x005000` |
| `otadata` | `0x00e000` | `0x002000` |
| `app0` | `0x010000` | `0x6d0000` |
| `app1` | `0x6e0000` | `0x6d0000` |
| `spiffs` | `0xdb0000` | `0x200000` |
| `coredump` | `0xff0000` | `0x010000` |

### 3.4 M3 port status: a finished firmware exists

The built binaries are in the
[`murphy-m3-v1`](https://github.com/mr-tbot/crosspoint-reader/releases/tag/murphy-m3-v1) release
(2026-07-29): `firmware.bin` (on top of the existing layout, `write-flash 0x10000`) and
`firmware-full-16MB.bin` (clean install, `write-flash 0x0`), plus `FLASHING.md` and SHA256 sums.

Claimed working: EPUB with the whole CrossPoint reader (pagination, TOC, bookmarks, progress, dictionary, OPDS, WiFi transfer, KOReader sync), MOBI/AZW with on-device conversion, PDF with reflow, an audio player, touch with gestures, **correct e-ink waveforms**, battery percentage, charge indication, frontlight, 5–10 pt fonts, and a UI fitted to the panel size.

The sober caveats:

- the build is **unofficial**, and the author says so plainly: "works well on my unit; no wider QA",
  with only a handful of downloads so far;
- Diirge (CrossPoint Team) on his own early port: "It works. I wouldn't recommend it. Display is so
  bad" — a complaint about the 240×416 (~130 ppi) panel itself, not about the quality of the port.

The fork's repository: <https://github.com/mr-tbot/Crosspoint-Murphy-M3>. It also holds the
**community-recovered M3 schematic**: `docs/hardware/Murphy_m3_reverse_schematic_PR2.pdf` (~530 KB).
There is no M4 equivalent, but that is exactly the document to obtain from corogoo or to recreate.

⚠️ **This firmware must not be flashed onto an M4.** It is fitted to the M3 panel at several levels at once: `Uc8253MurphyDriver` with the OEM LUTs of that specific glass, a 12,480-byte framebuffer (at X4 resolution the M4 would need 48,000), greyscale forcibly disabled, and a UI squeezed with `kUiDensityScale = 0.6` — with the 12–18 pt fonts physically stripped out of the image. The expected result is a black or garbage screen; the device survives and comes back from its own dump. Still, running someone else's waveforms on different glass for long is not advisable.

⚠️ **Dump privacy.** A full dump contains the NVS partition with saved WiFi passwords. Before publishing your own M4 dump, wipe NVS (`0x9000`–`0xE000`).

---

## 4. What is already upstream (important not to duplicate)

⚠️ All of this is **other people's open PRs**. Read and reuse them; keep your own changes in the fork.

### freeink-sdk (a submodule of this repository)

**[Free-Ink/freeink-sdk#25](https://github.com/Free-Ink/freeink-sdk/pull/25) — Add Murphy M3
(HamGeek M3 / 墨菲) hardware support** (OPEN, `mr-tbot`, 2026-07-29, +452/−110, 10 files).

The key point: **the SDK already contains a `MurphyM3` board profile and a `Uc8253MurphyDriver`** — several subsystems were stubbed out or wired to guessed values, and this PR fixes them against live hardware. Every finding in section 3 comes from it. The parts that are not Murphy specific and are useful for the M4 too:

- `PanelDriver::supportsGrayscale()` — a panel capability flag (without it `displayGray` draws the grey
  plane as a monochrome frame and the page comes out nearly black);
- `freeink::usbHostPresent()` — USB host detection without a dedicated pin;
- gesture thresholds scaled from the digitizer's coordinate range instead of fixed pixels;
- separation of the touch power/rails from the initialisation of a specific controller (previously
  entangled with the GT911 branch).

On the LUTs specifically: what used to live in `Uc8253MurphyLuts.h` was **not waveforms but voltage configuration blocks** (`0f8f4f…`) — no kick phase and no DC balance, hence the ghosting. The real OEM sets were extracted from the stock firmware. Fast update works **only as a complete package** (init variant `0x82=0x07`, `0x50=0xD7` plus the alternate LUT bank and the `0x17`/`0xA5` trigger); the same tables under the mode-0 init flash but never latch the image.

The maintainer (`itsthisjustin`) has already edited the PR so that it does not clash with other touch controllers, and asked the author to re-verify on an M3 — so the PR is in active work.

### crosspoint-reader (this repository)

**[#2802](https://github.com/crosspoint-reader/crosspoint-reader/pull/2802) — Murphy M3 support,
small-panel UI scaling, and native MOBI / PDF / audio** (OPEN, `mr-tbot`, 2026-07-30,
+176,879/−2,730, 100 files). The application half of the same port; it replaces the accidentally closed
[#2794](https://github.com/crosspoint-reader/crosspoint-reader/pull/2794). The author says outright that
the PR is being split up and that people should "take any subset". Inside:

- **UI density scaling** — theme metrics are run through `scaledMetrics()` at compile time, with a single
  knob `kUiDensityScale` (0.6 for the M3, 1.0 everywhere else) and a floor for touch targets;
- **a list hit-test bug that affects every device**: the leftover pixels below the last row belonged to no
  row, and taps there were silently lost;
- reader font sizes **down to 5 pt** plus 32 new faces;
- `--ink-floor` in `fontconvert.py`: on a 1-bit panel "weak" pixels are not pale but **absent** — at 7 pt
  about 20 % of a stroke's ink was being lost;
- **the frontlight** as a setting (Settings → Display → Frontlight) — before this CrossPoint had no
  frontlight support at all;
- native **MOBI/AZW** and **PDF** via on-device conversion to EPUB
  (`/.crosspoint/mobi_<hash>/`, `/.crosspoint/pdf_<hash>/`);
- an **audio player** on the ES8388, behind the `CROSSPOINT_AUDIO_PLAYER` flag.

Adjacent, but useful to us:

- **[#2880](https://github.com/crosspoint-reader/crosspoint-reader/pull/2880) — guard against
  cross-chip firmware installs** (OPEN, `Uri-Tauber`): neither the SD flasher nor OTA **checked the MCU
  family**, so an S3 image could be written to a C3 and brick the device. Exactly the class of accident
  that happened to Murphy owners on Reddit in bulk.
- **[#2472](https://github.com/crosspoint-reader/crosspoint-reader/pull/2472)** (CLOSED,
  `itsthisjustin`) — support for touch devices, the ESP32-S3 and UI auto-scaling;
  **[#2481](https://github.com/crosspoint-reader/crosspoint-reader/pull/2481)** (MERGED) —
  touch coordinate mapping; **[#2675](https://github.com/crosspoint-reader/crosspoint-reader/pull/2675)**
  (OPEN) — moving lists onto FreeInkUI plus touch-UI scaling.
- **[#2295](https://github.com/crosspoint-reader/crosspoint-reader/pull/2295)** (CLOSED) —
  battery/EPD/SD/touch for the m5paper: another example of an S3 profile.

**Conclusion for the M4:** touch, the S3, UI scaling for a different panel size, the frontlight and the wrong-chip flashing guard have already been written by other people. The M4 work comes down to a board profile (pins plus the panel driver) on top of that, not to a port from scratch.

---

## 4.1 The 800×480 panel ecosystem

The 4.26" 800×480 panel is the **Good Display GDEQ0426T82**, and it is long past being exotic in this project. The controller, however, drifts: vendors fit different chips in different production batches of the same model, which is why the SDK carries three drivers for one piece of glass.

| Driver in the SDK | Where it appears |
|---|---|
| `Ssd1677Driver` | Xteink X4, de-link, Sticky |
| `Uc8179Driver` | X4 / X4 Pro, a newer batch |
| `Uc8279X4Driver` | X4 Pro units where a UC8279 was fitted instead of the SSD1677 (**not to be confused** with `Uc8279Driver` for the X3, 792×528) |

That is why upstream gained controller auto-detection at boot
([#2707](https://github.com/crosspoint-reader/crosspoint-reader/pull/2707) — for the X3; the X4 Pro does
the same inside its profile). For the M4 this means the question is not "which panel" but "which of the
three controllers", and the answer can be obtained at runtime instead of guessed.

Devices on this panel that the SDK already supports: **Xteink X4** (C3), **Xteink X4 Pro** (S3),
**de-link** (S3), **Sticky** (S3, 3.97").

**What de-link is.** Not a finished reader but an open DIY kit by Ian Chasse
([iandchasse/de-link](https://github.com/iandchasse/de-link)): an ESP32-S3 board with a 24-pin connector
for any Good Display SPI panel (3.97", 4.26", 7.5"), 4-bit SDMMC, USB-C, a button array, optional
backlight-driver and battery-protection modules, and a printed case. Its S3 port and warm/cool frontlight
became the basis of the `DE_LINK` board support in the SDK
([`community-sdk-de-link`](https://github.com/iandchasse/community-sdk-de-link), branch `s3-port`).
For us it is proof that the combination **S3 + GDEQ0426T82 + SSD1677 + frontlight + SDMMC** already works.

---

## 4.2 Who is who, and why there will be no MurphyOS sources

Three names around this device get mixed up constantly:

| Name | Who they are | What you can get from them |
|---|---|---|
| **corogoo / MoFei / 摩菲** | the hardware developer | schematics and display-driver material — publicly promised (see 2.5); stock firmware on gitee |
| **HamGeek** (`hgeek.com`) | a reseller shop | nothing technical: their catalogue lists only the M3 3.7" and the RW01, **no 4.26"** |
| **pandacat** | a third-party team (Taiwan), author of MurphyOS / Panda AI OS | binaries; no sources |

**MurphyOS sources are not publicly available** — checked: none of the `crosspoint-reader` forks belongs to pandacat; searches on GitHub and Gitee turn up nothing; corogoo's gitee holds only built `.bin` files.

**And they cannot be demanded.** CrossPoint, freeink-sdk and the Murphy repository are all under **MIT** (copyright Dave Allie). MIT allows forking, closing and selling; the only obligation is to keep the licence text and the copyright notice. So the CrossPoint team's grievance with MurphyOS ("forked it, renamed it, added sudoku, even left the web server's HTML in") is about **attribution**, not about sources. Under the GPL the conversation would be different.

For the port none of this matters: the pins and waveforms come out of the binary, and with the log strings found above (see 2.3.1) even out of an ordinary serial log.

---

## 5. What to do when the device arrives

> The firmware analysis with the extracted pins is in [firmware-analysis.md](firmware-analysis.md).
> The device in plain words, what is ready and what has to be written, is in [anatomy.md](anatomy.md).
> The full plan with the hypothesis matrix, candidate profiles and the experiment tree is in
> [porting-plan.md](porting-plan.md). What follows is the short checklist.
>
> The subset of our findings prepared for `crosspoint-reader/Murphy` is in
> [upstream-pr/](../upstream-pr/README.md).

The order matters: take the dump **before** any reflashing.

- [ ] Ask the seller for the activation code for your UID (the "Activate Device" settings entry) — in case of a rollback
- [ ] **Ask the manufacturer for the M4 schematics** — corogoo publicly promised them to developers (see 2.5)
- [ ] Record the stock firmware version and its origin (MoFei `EPD426` vs MurphyOS)
- [ ] **Take a full flash dump**, `esptool.py read_flash 0 ALL murphy_m4_dump.bin`, and store it in two places
      (keep it private: NVS holds WiFi passwords; wipe `0x9000`–`0xE000` before publishing)
- [ ] Check that there is no flash encryption and no secure boot (the M3 has neither) — otherwise the dump is encrypted
- [ ] Record the chip and the sizes: `esptool.py flash_id`, `chip_id` (confirm the S3, the flash size, whether there is PSRAM)
- [ ] Parse the partition layout out of the dump and compare it with the M3
- [ ] Identify the panel: controller, resolution, LUTs (from the dump plus the FPC marking once opened)
- [ ] Scan I²C and compare with the M3 map (`0x10` ES8388, `0x2e` CHSC6x, `0x32` RX8010, `0x38` AHT30)
- [ ] Recover the pin map (display, touch, frontlight, SD, buttons, battery) following the `m3/findings/` template
- [ ] Check whether PSRAM is present and how much (it drives the whole memory policy in CLAUDE.md)
- [ ] Study the existing `MurphyM3` profile and `Uc8253MurphyDriver` in freeink-sdk as a template
- [ ] Build a CrossPoint board profile for the S3 and bring the display up

A project note: this repository's CLAUDE.md is written for the **ESP32-C3, 380 KB of RAM, no PSRAM**. On an S3 with PSRAM some of the hard constraints (a single framebuffer, the ban on `std::string`) stop being mandatory — but the project's rules must not be changed for the M4 in the shared branch; that belongs in a separate board profile.

Organisationally: all the work happens **in the fork** (`origin`, branch `device/murphy-m4`). Nothing goes upstream.

---

## 6. Useful addresses

| Resource | Link |
|---|---|
| Murphy reverse engineering (M3 + M4) | <https://github.com/crosspoint-reader/Murphy> |
| Fork with the M3 port and extra formats | <https://github.com/mr-tbot/Crosspoint-Murphy-M3> |
| Ready-made M3 firmware (binaries + `FLASHING.md`) | <https://github.com/mr-tbot/crosspoint-reader/releases/tag/murphy-m3-v1> |
| Community-recovered M3 schematic (PDF) | [`docs/hardware/Murphy_m3_reverse_schematic_PR2.pdf`](https://github.com/mr-tbot/Crosspoint-Murphy-M3/blob/main/docs/hardware/Murphy_m3_reverse_schematic_PR2.pdf) |
| OEM MoFei/corogoo firmware | <https://gitee.com/corogoo/3.7-inch-ink-screen-reader> |
| MurphyOS / firmware rollback | <https://murphy.pandacat.ai/tools/rollback> |
| CrossPoint web flasher (including for recovery) | <https://crosspointreader.com/#flash-tools> |
| Font converter (for the stock firmware) | <https://xteink.lakafior.com/> |

The full list of discussions reviewed is in [sources.md](sources.md).
