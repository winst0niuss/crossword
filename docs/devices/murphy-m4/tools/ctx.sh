#!/bin/zsh
# ctx.sh <PC_hex> [before] [after] — печатает согласованный дизассемблер вокруг PC
OBJ=~/.platformio/packages/toolchain-xtensa-esp-elf/bin/xtensa-esp32s3-elf-objdump
PC=$1; BEFORE=${2:-64}; AFTER=${3:-24}
PCD=$((PC))
best=3
for k in $(seq $BEFORE -1 3); do
  st=$((PCD-k))
  if $OBJ -D -b binary -m xtensa --adjust-vma=0x42000020 --start-address=$st --stop-address=$((PCD+3)) irom.bin 2>/dev/null | grep -q "^$(printf %x $PCD):"; then
    best=$k; break
  fi
done
$OBJ -D -b binary -m xtensa --adjust-vma=0x42000020 --start-address=$((PCD-best)) --stop-address=$((PCD+AFTER)) irom.bin | sed -n '7,80p'
