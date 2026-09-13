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

**Press animation**:
What a pad does at the moment it is pressed and released, chosen under Pads on
Appearance and saved with the layout. Separate from Pad style, which is how a pad
is drawn at rest. In the UI the row is labelled "Press".
_Avoid_: Effect, transition, feedback

**Edit on screen**:
The overlay's edit mode: drag to move, scroll to resize, click a pad to rebind.
_Avoid_: Move mode, unlock

**Undo**:
Single-level reversal of the last pad deletion only. Not a general edit history.
