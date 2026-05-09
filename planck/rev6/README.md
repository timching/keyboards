# Planck rev6 keymap — `timching_planck_rev6_drop`

Personal QMK keymap for the Planck rev6 Drop (ortho 4x12).

## Build

JSON is self-describing (`keyboard` + `keymap` fields), so no flags needed:

```bash
qmk compile ./timching_planck_rev6_drop.json
qmk flash   ./timching_planck_rev6_drop.json   # press reset on the board when prompted
```

## When to use the C path instead

Only after `qmk json2c` or hand-writing `keymap.c` for tap-dance, combos, or encoders:

```bash
qmk compile -kb planck/rev6_drop -km timching_planck_rev6_drop
```

For pure-JSON edits, stick with the first form — one less place to typo.
