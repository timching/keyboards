# Planck rev6 Drop — `timching` keymap

Personal QMK keymap for the Planck rev6 Drop (ortho 4×12).

See [`layers.md`](./layers.md) for visual layer reference.

## Build

JSON is self-describing (`keyboard` + `keymap` fields), so no flags needed:

```bash
qmk compile ./keymap.json
qmk flash   ./keymap.json   # press reset on the board when prompted
```

Compiled output goes to `binaries/firmware.bin`.

## When to use the C path instead

Only after `qmk json2c` or hand-writing `keymap.c` for tap-dance, combos, or encoders:

```bash
qmk compile -kb planck/rev6_drop -km timching
```

For pure-JSON edits, stick with the first form — one less place to typo.
