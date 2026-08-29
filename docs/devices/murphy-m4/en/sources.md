# Sources on the Murphy M3 / M4

The list of discussions and resources [README.md](README.md) was assembled from.
The "M3" / "M4" marker says which device is actually meant (titles are often misleading).

## Reddit — the submitted links

| # | Link | About | What is useful |
|---|---|---|---|
| 1 | [r/ereader — X4 Alternatives](https://www.reddit.com/r/ereader/comments/1stz4cd/x4_alternatives/) | — | **The Murphy is not mentioned.** The thread discusses the Obook5, Moaan Inkpalm 5, Pocketbook Verse, Xteink S4 |
| 2 | [r/ereader — For those that might be interested in the Murphy M4 ereader](https://www.reddit.com/r/ereader/comments/1u95oac/for_those_that_might_be_interested_in_the_murphy/) | M4 + M3 | The most substantial thread (86 comments): an M4 review, instructions for updating through the device's own web server, brick recovery, a link to the CrossPoint/Murphy repository, and Mr_Tbot's report of running CrossPoint on the M3 |
| 3 | [r/ereader — Help with Murphy 3.7 Cyrillic text](https://www.reddit.com/r/ereader/comments/1ulqodq/help_with_murphy_37_cyrillic_text/) | M3 | On stock firmware Cyrillic breaks words mid-line (the engine mishandles hyphenation because it treats the letters like Chinese characters); CrossPoint renders Cyrillic noticeably better |
| 4 | [r/ereader — My combo](https://www.reddit.com/r/ereader/comments/1unl2wb/my_combo/) | — | About the Xteink X4 + Crossink, not the Murphy. Contains a working scheme for syncing progress through KOReader Sync (`sync.koreader.rocks`, matching by filename) |
| 5 | [r/ereader — FAMUE BF07 vs Murphy 3.7](https://www.reddit.com/r/ereader/comments/1u5eays/famue_bf07_vs_murphy_37_long_battery_touch_light/) | M3 | Prices (~£55 / $75 for the Murphy), a pointer to the Murphy repository |
| 6 | [r/ereader — i had this tiny fella for 10 days…](https://www.reddit.com/r/ereader/comments/1ugwh33/i_had_this_tiny_fella_for_10_days_and_ive/) | — | A review of the Xteink X4; does not touch the Murphy |
| 7 | [r/ereader — This thing is actually pretty good](https://www.reddit.com/r/ereader/comments/1swxhxn/this_thing_is_actually_pretty_good/) | — | About the Musnap Neo (iReader Neo3), Android + KOReader. Unrelated to the Murphy |
| 8 | [r/pocketereaders — My e-ink babies](https://www.reddit.com/r/pocketereaders/comments/1ukxs2z/my_eink_babies/) | M3 + M4 | An owner of both the 3.7 and the 4.26: the current 3.7 firmware file is named `firmware_V532_E037_TOUCH.bin`; sellers send firmware out by direct message |
| 9 | [r/eink — Murphy M4 3.7 and XTEINK X4: compatibility and custom firmware](https://www.reddit.com/r/eink/comments/1td0wnn/murphy_m4_37_%D0%B8_xteink_x4_%D1%81%D0%BE%D0%B2%D0%BC%D0%B5%D1%81%D1%82%D0%B8%D0%BC%D0%BE%D1%81%D1%82%D1%8C_%D0%B8/) | M3 | In Russian. The seller's answer: the device is not locked and can be reflashed, but the firmware has to be adapted — the hardware differs from the X4 |
| 10 | [r/ereader — murphy 3 freezing](https://www.reddit.com/r/ereader/comments/1uvlblr/murphy_3_freezing/) | M3 | Bricked after flashing the wrong firmware from the repository; cured with firmware from the seller |
| 11 | [r/ereader — It's not perfect but it answers a need!](https://www.reddit.com/r/ereader/comments/1t7780l/its_not_perfect_but_it_answers_a_need/) | M3 (called the "M4 3.7") | Price ~$54, frontlight, touch; the old firmware had only 3 fonts and 3 sizes |
| 12 | [r/ereader — Any users of Murphy M4?](https://www.reddit.com/r/ereader/comments/1u39ssr/any_users_of_murphy_m4/) | M4 | Weight and size close to the X4; price $80–90 |
| 13 | [r/ereader — Better than XTEINK X4? (Murphy 3.7")](https://www.reddit.com/r/ereader/comments/1qs8v7q/better_than_xteink_x4_murphy_37/) | M3 | The earliest large thread (6 months old). Stock before the updates: extra spaces after apostrophes, no bold/italic, parts of the menu in Chinese. Links to a Chinese font tool |
| 14 | [r/xteinkereader — Murphy M4 3.7 vs XTEINK X4: hardware compatibility / firmware porting?](https://www.reddit.com/r/xteinkereader/comments/1td17q3/murphy_m4_37_vs_xteink_x4_hardware_compatibility/) | M3 + M4 | **Diirge (CrossPoint Team): "Working on crosspoint for the m3 right now… I need to get an m4 shipped to me to port to that"**; later, "It works. I wouldn't recommend it. Display is so bad". States the 3.7" resolution as 416×240 |
| 15 | [r/ereader — Thinking of getting Murphy M4 4.26" or should I wait for Xteink X4 Pro?](https://www.reddit.com/r/ereader/comments/1uknb56/thinking_of_getting_murphy_m4_426_or_should_i/) | M4 | The M4 versus the X4 Pro: USB-C+OTG against pogo pins, a ~2000 mAh battery against under 1000, the M4 fits an X4 case, no screws in the case (open it with heat, like the Xteink) |
| 16 | [r/ereader — Murphy M4 E-ink reader quick review next to Xteink X4](https://www.reddit.com/r/ereader/comments/1uh14ww/murphy_m4_eink_reader_quick_review_next_to_xteink/) | M4 | A detailed review: ~$80, ~220 ppi (the 3.7" has 120 ppi), warm light, a temperature/humidity sensor, 4 screen orientations, a dark theme; **every stock reflash requires a UID-tied activation code** |
| 17 | [r/ereader — Is there any users of Murphy M4?](https://www.reddit.com/r/ereader/comments/1tigh0t/is_there_any_users_of_murphy_m4/) | M4 + M3 | **Diirge: "the Murphy M4 already runs crosspoint… they forked our code, renamed it, and added sudoku… They even left the crosspointweb server html in the code"**. Stock versions up to v637 |

## Upstream PRs and issues

Reviewed through `gh` (read only). Nothing was submitted.

| Where | What | Status | Why it is useful |
|---|---|---|---|
| [freeink-sdk#25](https://github.com/Free-Ink/freeink-sdk/pull/25) | Add Murphy M3 (HamGeek M3 / 墨菲) hardware support, `mr-tbot` | OPEN | **The main technical source on M3 hardware.** The `MurphyM3` profile and `Uc8253MurphyDriver` were already in the SDK; the PR fixes SD (active-low power), touch (the GPIO43/45 gates, stop-separated reads, the axes), the OEM waveforms in place of voltage blocks, the 2.0 battery divider, USB host detection and the I²C peripheral map |
| [crosspoint-reader#2802](https://github.com/crosspoint-reader/crosspoint-reader/pull/2802) | Murphy M3 support, small-panel UI scaling, native MOBI/PDF/audio, `mr-tbot` | OPEN | The application half of the port: UI scaling for a small panel, fonts from 5 pt, `--ink-floor` for 1-bit panels, the frontlight as a setting, MOBI/AZW and PDF via conversion to EPUB, an ES8388 audio player, and the list hit-test bug |
| [crosspoint-reader#2794](https://github.com/crosspoint-reader/crosspoint-reader/pull/2794) | the same PR, previous iteration | CLOSED | Closed by accident while the branch was being rewritten |
| [crosspoint-reader#2311](https://github.com/crosspoint-reader/crosspoint-reader/issues/2311) | "Murphy M4: Development Related Notes" from **corogoo** (the manufacturer) | CLOSED | The manufacturer declares openness: **they are ready to provide hardware schematics** and display-driver material; MurphyOS by pandacat is not their firmware but a community CrossPoint port. The same issue holds [our question](https://github.com/crosspoint-reader/crosspoint-reader/issues/2311#issuecomment-5208195057) from 2026-08-06 and `itsthisjustin`'s reply: he has no hardware, does not offer schematics, and mentions "a fork where it works for someone" without specifics; he suggests bringing the SDK part into `freeink-sdk` |
| [crosspoint-reader#2880](https://github.com/crosspoint-reader/crosspoint-reader/pull/2880) | guard against cross-chip firmware installs, `Uri-Tauber` | OPEN | Checks the image's `chip_id` against the running partition — protection against exactly the brick Murphy owners kept hitting |
| [crosspoint-reader#2472](https://github.com/crosspoint-reader/crosspoint-reader/pull/2472) | touch devices, ESP32-S3, UI auto-scaling, `itsthisjustin` | CLOSED | Early S3/touch infrastructure |
| [crosspoint-reader#2481](https://github.com/crosspoint-reader/crosspoint-reader/pull/2481) | touch coordinate mapping + RTOS yielding | MERGED | Already upstream |
| [crosspoint-reader#2675](https://github.com/crosspoint-reader/crosspoint-reader/pull/2675) | lists on FreeInkUI + touch-UI scaling | OPEN | Overlaps with the UI half of the M3 port |
| [crosspoint-reader#2295](https://github.com/crosspoint-reader/crosspoint-reader/pull/2295) | battery/EPD/SD/touch for the m5paper | CLOSED | A second example of an S3 profile |

## Repositories and tools

| Resource | What is there |
|---|---|
| <https://github.com/crosspoint-reader/Murphy> | Firmware dumps and RE notes for the M3/M4. `m3/` — the full 16 MiB dump, pin map, flash layout, LUTs, port plan. `m4/` — the MurphyOS v1.2.16 OTA image, the evidence of CrossPoint lineage, the TTF rendering analysis, and web-UI assets |
| <https://github.com/mr-tbot/Crosspoint-Murphy-M3> | The fork with the M3 port plus PDF/MOBI/AZW and an audio player. Inside: submodules for crosspoint, freeink-sdk, community-sdk (branch `feat-support-for-m3`) and the Murphy repository, an analysis of the stock firmware and a deep dive into the port |
| [`murphy-m3-v1`](https://github.com/mr-tbot/crosspoint-reader/releases/tag/murphy-m3-v1) | **A ready CrossPoint firmware for the M3** (2026-07-29): `firmware.bin`, `firmware-full-16MB.bin`, `FLASHING.md`, SHA256. Unofficial, "no wider QA" |
| [`Murphy_m3_reverse_schematic_PR2.pdf`](https://github.com/mr-tbot/Crosspoint-Murphy-M3/blob/main/docs/hardware/Murphy_m3_reverse_schematic_PR2.pdf) | The community-recovered M3 schematic (~530 KB). There is no M4 equivalent |
| <https://www.hgeek.com/> | HamGeek, a reseller shop. The catalogue lists only the M3 3.7" ($69, sold out) and the RW01 mini; **there is no 4.26" model**. No sources or schematics exist under the HamGeek name |
| <https://gitee.com/corogoo/3.7-inch-ink-screen-reader> | OEM MoFei/corogoo firmware: `firmware/EPD426-v1` (for the 4.26") and `firmware/touch` (for the 3.7") |
| <https://murphy.pandacat.ai/> and `/tools/rollback` | MurphyOS ("Murphy Reader"), paid; the page for rolling back to stock |
| <https://crosspointreader.com/#flash-tools> | The browser-based CrossPoint flasher; used to recover bricked Murphys (X4 / X4 Pro profile plus a custom bin) |
| <https://xteink.lakafior.com/> | A converter from `.ttf`/`.otf` into the font format of the older stock firmware |
| <https://youtu.be/_DDLVtqr49I> | Video: CrossPoint running on a Murphy M3 |

## Checks that came back negative

Recorded so nobody has to look for them again:

- **There are no MurphyOS / Panda AI OS sources.** None of the `crosspoint-reader` forks belongs to
  pandacat; repository searches on GitHub ("murphy reader firmware", "pandacat") and Gitee come up
  empty; corogoo's gitee holds only built `.bin` files and a zip with a font tool.
- **There is no public fork with M4 support.** GitHub code search: `MurphyM4`, `murphy_m4`,
  `env:murphy_m4` — nothing; `Uc8253Murphy` is found only as the M3 driver (the SDK and vendored copies
  of it). Across the 39 forks of `freeink-sdk` and the `community-sdk`/`Murphy` branches the only
  relevant branch is `feat-support-for-m3`.
- **Nothing exists under the name "HamGeek M4".** The `hgeek.com` catalogue has only the M3 3.7"
  ($69, sold out) and the RW01 mini; there is no 4.26" model. GitHub/Gitee searches for "hamgeek"
  return only `crosspoint-reader/Murphy` and mr-tbot's fork.
- **The device model is not encoded inside the MurphyOS images** (neither 1.2.16 nor 2.2.7): no
  `M3`/`M4`, no `E426`/`E037`, no resolution strings. The OTA manifest returns `board: "mofei"` with
  no split.
- **Reddit is unreachable from the agent environment** — 403 for `WebFetch`, `curl`, `old.reddit.com`,
  `api.reddit.com` and readability proxies.

## How this was read

Reddit blocks direct requests from the agent environment (403 for `WebFetch`, `curl`, `old.reddit.com`, `api.reddit.com`). The threads were read by driving Chrome (the `claude-in-chrome` skill) on `old.reddit.com` with `?sort=top&limit=500` so that every branch expanded.
