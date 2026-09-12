# AZ-Overlay

A Windows input overlay that lights up on-screen pads as keys, controller buttons,
and sticks are used. This glossary fixes the words used in UI copy, docs, and code.

## Language

**Layout**:
A named, saved arrangement of pads, sticks, and appearance settings. Always exists
on disk; there is no unnamed layout.
_Avoid_: Profile (on-disk key only), preset, config

**Pad**:
One key or button cell on the overlay, placed in key units on a grid that may be
fractional (keyboards) or integer (Azeron).
_Avoid_: Key (ambiguous with the physical key that lights it), cell, button

**Stick**:
A directional control (thumbstick, analog stick, or d-pad) drawn as one element with
four direction inputs. Not a Pad.
_Avoid_: Joystick, hat

**Selection**:
The set of pads currently chosen for an action. One selection, shown in both the
pads table and the visual layout.

**Column** / **Row**:
As deletion targets: every pad whose centre on that axis lies within the selected
pad's span on that axis. Not a fixed integer band.

**Edit on screen**:
The overlay's edit mode: drag to move, scroll to resize, click a pad to rebind.
_Avoid_: Move mode, unlock

**Undo**:
Single-level reversal of the last pad deletion only. Not a general edit history.
