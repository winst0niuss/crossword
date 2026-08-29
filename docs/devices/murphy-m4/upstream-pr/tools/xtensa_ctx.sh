#!/usr/bin/env bash
# xtensa_ctx.sh IMAGE PC [BEFORE] [AFTER]
#
# Disassemble the IROM segment of an ESP32-S3 application image around PC,
# which is normally a call site reported by find_string_refs.py.
#
# Xtensa instructions are 2 or 3 bytes, so objdump started at an arbitrary
# offset decodes garbage. This walks the start point backwards until the
# instruction chain lands exactly on PC, then prints from there.
#
# Needs xtensa-esp32s3-elf-objdump. PlatformIO ships one:
#   ~/.platformio/packages/toolchain-xtensa-esp-elf/bin/
# Override with OBJDUMP=/path/to/xtensa-esp32s3-elf-objdump.
set -euo pipefail

IMAGE=${1:?usage: xtensa_ctx.sh IMAGE PC [BEFORE] [AFTER]}
PC=${2:?usage: xtensa_ctx.sh IMAGE PC [BEFORE] [AFTER]}
BEFORE=${3:-96}
AFTER=${4:-32}

OBJDUMP=${OBJDUMP:-$(command -v xtensa-esp32s3-elf-objdump || true)}
if [ -z "$OBJDUMP" ]; then
  OBJDUMP=$(ls -1 "$HOME"/.platformio/packages/toolchain-xtensa-esp-elf/bin/xtensa-esp32s3-elf-objdump 2>/dev/null | head -1 || true)
fi
[ -x "$OBJDUMP" ] || { echo "xtensa-esp32s3-elf-objdump not found; set OBJDUMP=" >&2; exit 1; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Carve the IROM segment out of the image and report its load address.
VMA=$(python3 - "$IMAGE" "$TMP/irom.bin" <<'PYEOF'
import struct, sys
data = open(sys.argv[1], 'rb').read()
seg_count = data[1]
off = 24
for _ in range(seg_count):
    load_addr, length = struct.unpack('<II', data[off:off + 8])
    off += 8
    if 0x42000000 <= load_addr < 0x44000000:
        open(sys.argv[2], 'wb').write(data[off:off + length])
        print(hex(load_addr))
        break
    off += length
else:
    sys.exit('no IROM segment in image')
PYEOF
)

PCD=$((PC))
start=$((PCD - 3))
for k in $(seq "$BEFORE" -1 3); do
  cand=$((PCD - k))
  if "$OBJDUMP" -D -b binary -m xtensa --adjust-vma="$VMA" \
       --start-address=$cand --stop-address=$((PCD + 3)) "$TMP/irom.bin" 2>/dev/null \
       | grep -q "^ *$(printf %x $PCD):"; then
    start=$cand
    break
  fi
done

"$OBJDUMP" -D -b binary -m xtensa --adjust-vma="$VMA" \
  --start-address=$start --stop-address=$((PCD + AFTER)) "$TMP/irom.bin" | sed -n '7,200p'
