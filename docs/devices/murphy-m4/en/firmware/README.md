# Murphy firmware archive

Local copies of the factory firmware. They are kept in the repository because the sources are unreliable: the `murphy.pandacat.ai` `/ota/latest` manifest names **only the current** version, and no index of earlier builds is published anywhere. The files themselves are still served at their original direct URLs (checked on 2026-08-29: `panda-ai-os-2.2.7.bin` returned HTTP 200 weeks after 2.3.5 replaced it), but that address can only be known if it was recorded in advance.

⚠️ These are **other people's proprietary binaries**, published openly by their authors. They are kept here as raw material for reverse engineering and as a means of recovering the device.

## Contents

| File | Size | What for | Origin |
|---|---:|---|---|
| `panda-ai-os-2.3.5.bin` | 4,319,904 | **Panda AI OS**, current as of 2026-08-29. Prints its whole pin map to the boot log; its constants are more complete than 2.2.7's | `https://murphy.pandacat.ai/firmware/panda-ai-os-2.3.5.bin` (the address came from `/ota/latest`) |
| `panda-ai-os-2.2.7.bin` | 6,009,744 | The previous Panda AI OS (current as of 2026-08-07). **An 800×480 panel → this is the M4.** The pinout was first extracted from it | `https://murphy.pandacat.ai/firmware/panda-ai-os-2.2.7.bin` |
| `murphy-26-0526-1.2.16.bin` | 3,903,024 | The previous MurphyOS ("Murphy Reader" v1.2.16, built 2026-05-26). The one on which the CrossPoint team proved the kinship with their code | `crosspoint-reader/Murphy`, file in `m4/` |
| `mofei-corogoo-EPD426-v1.bin` | 5,626,704 | **The factory OEM firmware from MoFei/corogoo for the 4.26"** — the alternative to MurphyOS on the same hardware | `crosspoint-reader/Murphy`, file in `m3/oem_firmware/` (it sits there as the "big brother", despite the path) |
| `mofei-corogoo-touch-v525.bin` | 2,907,200 | The factory OEM for the **3.7" (M3)**. Kept for comparison: it shows what differs between the models | `crosspoint-reader/Murphy`, file in `m3/oem_firmware/` |

## Checksums (SHA-256)

```
d049bfc8e5d44c8f0be6c8f69855a9b36954e3df053ffecaa5b86dfe449dfebd  panda-ai-os-2.3.5.bin
089b10973938bdf5f05b8910853a851a1cae586ce68516a50bc4c6871e44c458  panda-ai-os-2.2.7.bin
3ee3d0a7207a17d49eb47fa60febff8cf4ac2f47bb52d74a1beceb40b8b124ea  murphy-26-0526-1.2.16.bin
e932fbc697339f3b1e17adcb6a77e11ba50a1ec2297c20a4fbf30a667759fa50  mofei-corogoo-EPD426-v1.bin
```

All four were checked against the manifests and the notes in the Murphy repository. To verify:

```bash
shasum -a 256 *.bin
```

## What is not here, and why

- **A dump of our own device.** It will appear once the M4 arrives — but a full dump contains the NVS
  partition with Wi-Fi passwords, so it reaches the repository only after `0x9000`–`0xE000` has been
  wiped, or not at all.
- **CrossPoint builds for the M3** (the `murphy-m3-v1` release) — they are not ours and are unusable
  on the M4.

## How to use this

The analysis and the extracted constants are in [../firmware-analysis.md](../firmware-analysis.md), the scripts in [../tools/](../tools/). Quick start:

```bash
python3 ../tools/espimg.py panda-ai-os-2.3.5.bin
```

These files are **not** suitable for recovering the device directly: an OTA image is written not at address zero but at `app_offset` (`0x20000` for MurphyOS), and the stock OS additionally demands a UID-tied activation code. The reliable way back is your own dump of the entire flash, taken before any experiments.
