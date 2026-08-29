# What an e-reader is made of, and which software we already have

In plain language: what hardware sits inside the Murphy M4, what each part is for, and which parts already have code written by other people versus which we will have to write ourselves.

---

## 1. Device diagram

```
                        ┌───────────────────────────┐
                        │     ESP32-S3 (the brain)  │
                        │  two cores, Wi-Fi, USB-C  │
                        └─────────────┬─────────────┘
                                      │
        ┌───────────────┬─────────────┼──────────────┬───────────────┐
        │               │             │              │               │
   ╔════▼════╗    ╔═════▼════╗   ╔════▼════╗   ╔═════▼═════╗  ╔══════▼═════╗
   ║ SCREEN  ║    ║  TOUCH   ║   ║ SD CARD ║   ║ FRONTLIGHT║  ║  BUTTONS   ║
   ║ e-ink   ║    ║ FT6336U  ║   ║ (books) ║   ║  warm /   ║  ║            ║
   ║ 800×480 ║    ║          ║   ║         ║   ║  cool     ║  ║            ║
   ╚═════════╝    ╚══════════╝   ╚═════════╝   ╚═══════════╝  ╚════════════╝
      6 wires        4 wires        6 wires       2 wires      one wire
      SPI            I²C            SDMMC         PWM          per button

        ┌───────────────┬──────────────────────┬──────────────────┐
   ╔════▼════╗    ╔═════▼═════╗          ╔═════▼═════╗      ╔═════▼═════╗
   ║ FLASH   ║    ║ BATTERY   ║          ║  CLOCK    ║      ║  SENSOR   ║
   ║ 16 MB   ║    ║ + charger ║          ║  (RTC)    ║      ║ temp/hum  ║
   ║(firmware)║   ║           ║          ║           ║      ║           ║
   ╚═════════╝    ╚═══════════╝          ╚═══════════╝      ╚═══════════╝
```

---

## 2. What each part does

| Part | In plain words | How it is wired |
|---|---|---|
| **ESP32-S3** | The main chip. It runs the firmware: reads the book from the card, lays the text out into pages, draws them on the screen | — |
| **16 MB flash** | Built-in memory holding the firmware itself. Books are not written here | inside the chip |
| **E-ink screen** | The image holds without power; changing it means "pumping" the pixels through a special recipe | 6 SPI lines |
| **Touchscreen** | A separate chip on top of the screen: it reports finger coordinates | 4 I²C lines |
| **SD card** | Where the books, fonts and page cache live | 6 SDMMC lines |
| **Frontlight** | LEDs along the edge of the glass. Brightness and "warmth" are set by PWM, i.e. fast blinking | 2 PWM lines |
| **Buttons** | Page turns, power, reset | one line each |
| **Battery** | The chip measures the voltage through a divider and converts it to a percentage | 1 ADC line |
| **Clock (RTC)** | Keeps ticking even while the device sleeps | I²C |
| **Sensor** | Temperature and humidity, for the clock screen | I²C |

### Why the screen is the hardest part

An ordinary display simply receives an image. E-ink works differently: black and white particles float inside, and moving them means applying a **sequence of pulses at different voltages** to the glass — that is the "waveform" (a LUT, lookup table).

- Wrong pulses → the image does not latch, or "ghosts" of the previous page remain.
- Every model of glass has its own recipe.
- This is exactly where the Murphy M3 port lost the most time: what everyone took for a pulse table
  turned out to be a voltage table — no "kick" at the start and no charge balancing, hence the dirty
  background.

Conclusion: everything else is "connecting wires in code", while the screen is the one place that needs a recipe you cannot guess.

---

## 3. What software is ready and what has to be written

Legend: ✅ ready, taken as is · ⚙️ exists, needs configuring for our pins · ✍️ has to be written · ❓ still unknown

| Part | Status | Notes |
|---|---|---|
| EPUB reading, page layout, fonts, table of contents, bookmarks, progress | ✅ | This is CrossPoint itself, the whole point of the project. Nothing to touch |
| Wi-Fi, web server, OPDS, KOReader sync | ✅ | Already in the firmware |
| ESP32-S3 support | ✅ | Supported: the X4 Pro, Sticky, de-link and M3 all run on it |
| 800×480 screen | ✅ | This panel is already supported (X4, X4 Pro, de-link, Sticky) |
| **Screen controller** | ❓ | There are three kinds on this panel. All three are already written — we just need to learn which one we have |
| Waveforms (LUTs) | ✅ | They ship with the controller driver |
| SD card (4 lines) | ⚙️ | The code exists; fill in our pins |
| Buttons | ⚙️ | The code exists; fill in our pins |
| Warm/cool frontlight | ⚙️ | The code exists (as on the X4 Pro); fill in our pins |
| Battery | ⚙️ | The code exists; fill in the pin and the divider |
| **FT6336U touchscreen** | ✍️ | **The only thing missing.** The SDK has GT911 and CHSC6x, not ours |
| Clock (RTC) | ✍️ | No driver, not even for the M3. It does not stop you reading books, so it can wait |
| Temperature sensor | ✍️ | The same: nice to have, not required |
| Audio | ✍️ | The M3 has it (ES8388 codec); nobody has checked the M4. Not required |

### Summary

```
   ✅ Ready ~80 %    ── reading books, Wi-Fi, a screen of this size, the S3
   ⚙️ Configure      ── SD, buttons, frontlight, battery  (fill in the pins)
   ✍️ Write          ── the FT6336U touchscreen driver
   ❓ Find out       ── which of the three screen controllers is fitted
```

---

## 4. Two layers of firmware: CrossPoint and the FreeInk SDK

The firmware is built from two projects, not one, and that split is exactly what makes our port feasible.

```
   ┌───────────────────────────────────────────────────────┐
   │  CrossPoint Reader — THE APPLICATION                  │
   │  the "reader": bookshelves, EPUB, pages, fonts,       │
   │  bookmarks, dictionary, settings, Wi-Fi, OPDS         │
   │                                                       │
   │  Does not know which pin the screen is soldered to.   │
   │  It says: "draw this page", "give me the key press"   │
   └───────────────────────┬───────────────────────────────┘
                           │  one shared API
   ┌───────────────────────▼───────────────────────────────┐
   │  FreeInk SDK — THE SHARED PART (freeink-sdk/ folder)  │
   │  everything reused across different devices           │
   │                                                       │
   │  display/   panel drivers: SSD1677, UC8253, …         │
   │  hardware/  BoardConfig, InputManager, BatteryMonitor,│
   │             SDCardManager, FrontlightManager, Rtc, …  │
   │  network/   Wi-Fi, TLS                                │
   │  ui/        FreeInkUI: keyboard, lists, dialogs,      │
   │             panels, controls                          │
   │  book/      book file handling, content protection    │
   └───────────────────────┬───────────────────────────────┘
                           │
                   Murphy M4 HARDWARE
```

⚠️ **An important clarification about the boundary.** The SDK is not "the hardware-only part". The line is drawn on a different criterion:

> **the SDK holds what any firmware built on this SDK needs; the application holds what is specific
> to one particular reader.**

That is why, for example, **the keyboard lives in the SDK** (`libs/ui/FreeInkUI/include/components/keyboard/`): every device needs to type a Wi-Fi password or an OPDS address. Its language layouts belong there too, and the maintainers insist on this: a new `KeyboardLayoutId` member plus tables in `builtinKeyboardLayout()` (`libs/ui/FreeInkUI/src/FreeInkUI.cpp`), leaving a single line in `layoutForLanguage()` in the firmware. Attempts to put layout tables into `KeyboardEntryActivity` are rejected in review regardless of code quality.

`KeyboardEntryActivity` in this repository is already a concrete screen of one concrete reader: it only calls the ready component from the SDK.

### Why the split exists

Imagine the reader had been written directly "for the Xteink X4". Pin numbers and panel commands would be smeared across the whole codebase, and porting to another device would mean rewriting half the firmware. That is how it used to be — CrossPoint started as firmware for exactly one device.

The FreeInk SDK moved everything shared into a separate layer with a simple rule:

> **Adding a new device means adding data (a board profile and driver settings), not editing shared code.**

The `BoardProfile` is that data: the pin list, the screen controller type, the panel size, how buttons are read, the frontlight parameters. The application knows nothing about it: it calls `renderer.drawText(...)` and the SDK turns that into pulses on the specific wires of a specific panel.

### What that means for us

| Question | Answer |
|---|---|
| Do we have to modify the reader itself? | **No.** The EPUB, page, font and Wi-Fi logic is the same for every device |
| Where do our changes go? | Almost everything into `freeink-sdk`: the M4 board profile plus the FT6336U touch driver. The same route the keyboard layouts took |
| Why is this quick? | The 800×480 panel and the ESP32-S3 are already supported in the SDK (X4, X4 Pro, de-link, Sticky) — we take what exists |
| What the maintainer said | In so many words: *"porting the sdk pieces over here would be ideal"* — the result is expected in the SDK |

### Where it lives and how it is wired in

`freeink-sdk/` at the project root is a **git submodule** (a separate repository, `Free-Ink/freeink-sdk`, also MIT). In `platformio.ini` its libraries are linked in by reference:

```ini
BatteryMonitor=symlink://freeink-sdk/libs/hardware/BatteryMonitor
EInkDisplay=symlink://freeink-sdk/libs/display/FreeInkDisplay
BoardConfig=symlink://freeink-sdk/libs/hardware/BoardConfig
...
```

An important consequence: **M4 hardware changes are committed to your own SDK fork**, not to this repository. You already have such a fork — `winst0niuss/freeink-sdk` — and one PR to it (the keyboard layouts) has already been accepted.

---

## 5. What this looks like in code

The entire "device configuration" is a single 30-line struct listing the pins. An example from the SDK (another device's profile):

```cpp
constexpr BoardProfile DE_LINK = {
    Board::DeLink,
    "de_link",
    InputStyle::XteinkAdcLadder,       // how the buttons are read
    DisplayController::SSD1677,        // which screen controller
    800, 480,                          // panel size
    {8, 10, 21, 4, 5, 6, ...},         // screen pins: SCLK, MOSI, CS, DC, RST, BUSY
    ...                                // then SD, buttons, battery, frontlight, touch
};
```

For the M4 nearly all of these numbers are **already known** — extracted from the factory firmware (see [firmware-analysis.md](firmware-analysis.md)):

| What | Pins |
|---|---|
| Screen | SCLK=4, MOSI=3, CS=5, DC=6, RST=7, BUSY=8 |
| Touch | SDA=13, SCL=12, INT=44, power=45 (enabled by a low level) |
| Battery | ADC on 9 |
| SD | 4 data lines, 20 MHz |
| Panel | 800×480, 48,000-byte frame |

---

## 6. Order of work

1. **Take a copy of the factory firmware** — insurance: whatever breaks, the device comes back to life.
2. **Power it on and read the log** — the firmware prints its own pins; compare against the table above.
3. **Identify the screen controller** — and take the existing driver.
4. **Fill in the struct** with the pins → CrossPoint boots and turns pages.
5. **Write the touch driver** — after that the device is fully usable.
6. The rest (clock, sensor, audio) is optional.

The detailed plan with commands is in [porting-plan.md](porting-plan.md).
